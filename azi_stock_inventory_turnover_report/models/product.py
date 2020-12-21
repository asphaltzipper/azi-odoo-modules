from dateutil.relativedelta import relativedelta
import datetime
from odoo import fields, models


class Product(models.Model):
    _inherit = "product.product"

    average_cost_6m = fields.Float(compute="_compute_inventory_turn_report",
                                   help="Average cost of inventory in the last 6 months")
    average_cost_12m = fields.Float(compute="_compute_inventory_turn_report",
                                    help="Average cost of inventory in the last 12 months")
    consumed_cost_6m = fields.Float(compute="_compute_inventory_turn_report",
                                    help="Consumed cost in the last 6 months")
    consumed_cost_12m = fields.Float(compute="_compute_inventory_turn_report",
                                     help="Consumed cost in the last 12 months")

    def get_average_cost_and_turns(self, product_id):
        query = """
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
                and pt.active=true and pp.id = %s
            )
            select
                a.product_id,
                a.category_id,
                (coalesce(b6.balance, 0.0) + coalesce(e.balance, 0.0)) / 2 as avg_6_balance,
                (coalesce(b12.balance, 0.0) + coalesce(e.balance, 0.0)) / 2 as avg_12_balance,
                coalesce(c6.credit, 0.0) as consumed_6_cost,
                coalesce(c12.credit, 0.0) as consumed_12_cost,
                case when ( (coalesce(b6.balance, 0.0) + coalesce(e.balance, 0.0)) / 2 ) <> 0.0 then
                    coalesce(c6.credit, 0.0) / ( (coalesce(b6.balance, 0.0) + coalesce(e.balance, 0.0)) / 2 )
                    else 0.0 end as turns_6,
                case when ( (coalesce(b12.balance, 0.0) + coalesce(e.balance, 0.0)) / 2 ) <> 0.0 then
                    coalesce(c12.credit, 0.0) / ( (coalesce(b12.balance, 0.0) + coalesce(e.balance, 0.0)) / 2 )
                    else 0.0 end as turns_12
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
                select
                    a.product_id,
                    sum(aml.balance) as balance
                from a
                left join account_move_line as aml on aml.product_id=a.product_id and aml.account_id=a.account_id
                where date < now() - interval '6 months'
                group by a.product_id
            ) as b6 on a.product_id=b6.product_id
            left join (
                select
                    a.product_id,
                    sum(aml.balance) as balance
                from a
                left join account_move_line as aml on aml.product_id=a.product_id and aml.account_id=a.account_id
                where date < now() - interval '12 months'
                group by a.product_id
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
        """
        self.env.cr.execute(query, [str(product_id)])
        _, _, avg_cost_6m, avg_cost_12m, consumed_cost_6m, consumed_cost_12m, inventory_turns_6m, \
            inventory_turns_12_m = self.env.cr.fetchall()[0]
        return avg_cost_6m, avg_cost_12m, consumed_cost_6m, consumed_cost_12m, inventory_turns_6m, inventory_turns_12_m

    def _compute_inventory_turn_report(self):
        month = relativedelta(months=1)
        today = fields.Date.today()
        at_6m_ago = today - 6 * month
        at_12m_ago = today - 12 * month
        available6m = {
            x.id: x.qty_available
            for x in self.with_context(to_date=at_6m_ago)}
        available12m = {
            x.id: x.qty_available
            for x in self.with_context(to_date=at_12m_ago)}
        gotten6m = self._compute_quantities_in_dict(from_date=at_6m_ago)
        gotten12m = self._compute_quantities_in_dict(from_date=at_12m_ago)
        for prod in self:
            avg_cost_6m, avg_cost_12m, consumed_cost_6m, consumed_cost_12m, inventory_turns_6m, \
                inventory_turns_12_m = self.get_average_cost_and_turns(prod.id)
            prod.total_cost = prod.qty_available * prod.standard_price
            # average inventory balance
            prod.average_cost_6m = avg_cost_6m
            prod.average_cost_12m = avg_cost_12m
            # Quantity initially available
            prod.qty_available_6m = available6m.get(prod.id)
            prod.qty_available_12m = available12m.get(prod.id)
            # Quantity gotten (produced + procured)
            prod.qty_gotten_6m = gotten6m.get(prod.id)
            prod.qty_gotten_12m = gotten12m.get(prod.id)
            # Quantity consumed in period
            prod.qty_consumed_6m = (
                    prod.qty_available_6m
                    + prod.qty_gotten_6m
                    - prod.qty_available)
            prod.qty_consumed_12m = (
                    prod.qty_available_12m
                    + prod.qty_gotten_12m
                    - prod.qty_available)
            # Months of Inventory
            prod.months_of_inventory_6m = (
                0.0 if not prod.qty_consumed_6m else
                prod.qty_available / prod.qty_consumed_6m * 6)
            prod.months_of_inventory_12m = (
                0.0 if not prod.qty_consumed_12m else
                prod.qty_available / prod.qty_consumed_12m * 12)
            # Consumed Cost
            prod.consumed_cost_6m = consumed_cost_6m
            prod.consumed_cost_12m = consumed_cost_12m
            # Turns / Cycles per Month
            prod.inventory_turns_6m = inventory_turns_6m
            prod.inventory_turns_12m = inventory_turns_12_m


class ProductCategory(models.Model):
    _inherit = 'product.category'

    average_cost_6m = fields.Float(compute="_compute_inventory_turn_report",
                                   help="Average cost of inventory in the last 6 months")
    average_cost_12m = fields.Float(compute="_compute_inventory_turn_report",
                                    help="Average cost of inventory in the last 12 months")
    consumed_cost_6m = fields.Float(compute="_compute_inventory_turn_report",
                                    help="Consumed cost in the last 6 months")
    consumed_cost_12m = fields.Float(compute="_compute_inventory_turn_report",
                                     help="Consumed cost in the last 12 months")
    inventory_turns_6m = fields.Float(compute="_compute_inventory_turn_report",
                                      help="Inventory Turns / Cycles in the last 6 months")
    inventory_turns_12m = fields.Float(compute="_compute_inventory_turn_report",
                                       help="Inventory Turns / Cycles in the last 12 months")

    def get_average_cost_and_turns(self, category_id):
        query = """
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
                and pt.active=true and pc.id = %s
            )
            select
                a.product_id,
                a.category_id,
                (coalesce(b6.balance, 0.0) + coalesce(e.balance, 0.0)) / 2 as avg_6_balance,
                (coalesce(b12.balance, 0.0) + coalesce(e.balance, 0.0)) / 2 as avg_12_balance,
                coalesce(c6.credit, 0.0) as consumed_6_cost,
                coalesce(c12.credit, 0.0) as consumed_12_cost,
                case when ( (coalesce(b6.balance, 0.0) + coalesce(e.balance, 0.0)) / 2 ) <> 0.0 then
                    coalesce(c6.credit, 0.0) / ( (coalesce(b6.balance, 0.0) + coalesce(e.balance, 0.0)) / 2 )
                    else 0.0 end as turns_6,
                case when ( (coalesce(b12.balance, 0.0) + coalesce(e.balance, 0.0)) / 2 ) <> 0.0 then
                    coalesce(c12.credit, 0.0) / ( (coalesce(b12.balance, 0.0) + coalesce(e.balance, 0.0)) / 2 )
                    else 0.0 end as turns_12
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
                select
                    a.product_id,
                    sum(aml.balance) as balance
                from a
                left join account_move_line as aml on aml.product_id=a.product_id and aml.account_id=a.account_id
                where date < now() - interval '6 months'
                group by a.product_id
            ) as b6 on a.product_id=b6.product_id
            left join (
                select
                    a.product_id,
                    sum(aml.balance) as balance
                from a
                left join account_move_line as aml on aml.product_id=a.product_id and aml.account_id=a.account_id
                where date < now() - interval '12 months'
                group by a.product_id
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
        """
        self.env.cr.execute(query, [str(category_id)])
        avg_cost_6m = avg_cost_12m = consumed_cost_6m = consumed_cost_12m = inventory_turns_6m = \
            inventory_turns_12_m = 0
        for turn_values in self.env.cr.fetchall():
            avg_cost_6m += turn_values[2]
            avg_cost_12m += turn_values[3]
            consumed_cost_6m += turn_values[4]
            consumed_cost_12m += turn_values[5]
            inventory_turns_6m += turn_values[6]
            inventory_turns_12_m += turn_values[7]
        return avg_cost_6m, avg_cost_12m, consumed_cost_6m, consumed_cost_12m, inventory_turns_6m, inventory_turns_12_m

    def _compute_inventory_turn_report(self):
        for category in self:
            avg_cost_6m, avg_cost_12m, consumed_cost_6m, consumed_cost_12m, inventory_turns_6m, \
                inventory_turns_12_m = self.get_average_cost_and_turns(category.id)
            # average inventory balance
            category.average_cost_6m = avg_cost_6m
            category.average_cost_12m = avg_cost_12m
            # Consumed Cost
            category.consumed_cost_6m = consumed_cost_6m
            category.consumed_cost_12m = consumed_cost_12m
            # Turns / Cycles per Month
            category.inventory_turns_6m = inventory_turns_6m
            category.inventory_turns_12m = inventory_turns_12_m
