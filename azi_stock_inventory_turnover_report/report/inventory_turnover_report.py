from odoo import api, fields, models, tools


class InventoryProductTurnover(models.Model):
    _name = "inventory.product.turnover"
    _description = 'Inventory Turnover Report'
    _auto = False

    product_id = fields.Many2one('product.product', 'Product')
    category_id = fields.Many2one('product.category', 'category')
    avg_6_balance = fields.Float(
        string="6mo Avg Balance",
        help="Average balance over the last 6 months",
    )
    avg_12_balance = fields.Float(
        string="12mo Avg Balance",
        help="Average balance over the last 12 months",
    )
    consumed_6_cost = fields.Float(
        string="6mo Usage",
        help="Consumed cost in the last 6 months",
    )
    consumed_12_cost = fields.Float(
        string="12mo Usage",
        help="Consumed cost in the last 12 months",
    )
    turns_6m = fields.Float(
        string="6mo Turns",
        help="Inventory turns in the last 6 months"
    )
    turns_12m = fields.Float(
        string="12mo turns",
        help="Inventory turns in the last 12 months",
    )
    current_balance = fields.Float(
        string="Current Balance",
        help="Current inventory balance",
    )

    @api.depends('avg_6_balance', 'avg_12_balance', 'consumed_6_cost', 'consumed_12_cost')
    def _compute_turns(self):
        for record in self:
            record.turns_6m = record.avg_6_balance and record.consumed_6_cost / record.avg_6_balance or 0.0
            record.turns_12m = record.avg_12_balance and record.consumed_12_cost / record.avg_12_balance or 0.0

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'inventory_product_turnover')
        self._cr.execute("""
            CREATE VIEW inventory_product_turnover AS (
                with a as (
                    select
                        pp.id as product_id,
                        pc.id as category_id,
                        aa.id as account_id
                    from product_product pp
                    left join product_template pt on pt.id=pp.product_tmpl_id
                    left join product_category as pc on pc.id=pt.categ_id
                    left join ir_property as ip on ip.res_id='product.category,'||pt.categ_id and ip.name='property_stock_valuation_account_id'
                    left join account_account as aa on 'account.account,'||aa.id=ip.value_reference
                    where pt.type='product'
                    and pt.active=true
                ),
                b as (
                    -- sum of transactions grouped by day
                    select
                        a.product_id,
                        aml.date as sum_day,
                        sum(aml.balance) as day_balance
                    from a
                    left join account_move_line aml on aml.product_id=a.product_id and aml.account_id=a.account_id
                    group by a.product_id, aml.date
                ),
                c as (
                    -- daily balance
                    -- i.e. running cummulative sum of daily transactions
                    select
                        product_id,
                        sum_day,
                        day_balance,
                        sum(day_balance) over (partition by product_id order by sum_day asc rows between unbounded preceding and current row) as cummulative_balance
                    from b
                )
                select
                    a.product_id as id,
                    a.product_id,
                    a.category_id,
                    round(coalesce(e.balance, 0.0), 0) as current_balance,
                    round((coalesce(b6.balance, 0.0) + coalesce(e.balance, 0.0)) / 2, 0) as avg_6_balance,
                    round((coalesce(b12.balance, 0.0) + coalesce(b6.balance, 0.0) + coalesce(e.balance, 0.0)) / 3, 0) as avg_12_balance,
                    round(coalesce(c6.credit, 0.0), 0) as consumed_6_cost,
                    round(coalesce(c12.credit, 0.0), 0) as consumed_12_cost,
                    case when round(((coalesce(b6.balance, 0.0) + coalesce(e.balance, 0.0)) / 2), 0) <> 0.0
                         then abs(round((coalesce(c6.credit, 0.0)) / ((coalesce(b6.balance, 0.0) + coalesce(e.balance, 0.0)) / 2), 2))
                         else 0.0 end as turns_6m,
                    case when round(((coalesce(b12.balance, 0.0) + coalesce(b6.balance, 0.0) + coalesce(e.balance, 0.0)) / 3), 0) <> 0.0
                         then abs(round((coalesce(c12.credit, 0.0)) / ((coalesce(b12.balance, 0.0) + coalesce(b6.balance, 0.0) + coalesce(e.balance, 0.0)) / 3), 2))
                         else 0.0 end as turns_12m
                from a
                left join (
                    select
                        a.product_id,
                        sum(aml.balance) as balance
                    from a
                    left join account_move_line as aml on aml.product_id=a.product_id and aml.account_id=a.account_id
                    group by a.product_id
                ) as e on e.product_id=a.product_id
                left join (
                    -- average daily balance for prior 6 months
                    select
                        product_id,
                        avg(cummulative_balance) as balance
                    from c
                    where sum_day >= now() - interval '6 months'
                    group by product_id
                ) as b6 on a.product_id=b6.product_id
                left join (
                    -- average daily balance for prior 12 months
                    select
                        product_id,
                        avg(cummulative_balance) as balance
                    from c
                    where sum_day >= now() - interval '12 months'
                    group by product_id
                ) as b12 on a.product_id=b12.product_id
                left join (
                    select
                        a.product_id,
                        sum(aml.credit) as credit
                    from a
                    left join account_move_line as aml on aml.product_id=a.product_id and aml.account_id=a.account_id
                    where date >= now() - interval '6 months'
                    group by a.product_id
                ) as c6 on c6.product_id=a.product_id
                left join (
                    select
                        a.product_id,
                        sum(aml.credit) as credit
                    from a
                    left join account_move_line as aml on aml.product_id=a.product_id and aml.account_id=a.account_id
                    where date >= now() - interval '12 months'
                    group by a.product_id
                ) as c12 on c12.product_id=a.product_id
            )
        """)
