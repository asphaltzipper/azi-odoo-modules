from dateutil.relativedelta import relativedelta
import datetime
from odoo import fields, models


class Product(models.Model):
    _inherit = "product.product"

    average_cost_6m = fields.Float(
        compute="_compute_inventory_turn_report",
        help="Average cost of inventory in the last 6 months")
    average_cost_12m = fields.Float(
        compute="_compute_inventory_turn_report",
        help="Average cost of inventory in the last 12 months")
    consumed_cost_6m = fields.Float(
        compute="_compute_inventory_turn_report",
        help="Consumed cost in the last 6 months")
    consumed_cost_12m = fields.Float(
        compute="_compute_inventory_turn_report",
        help="Consumed cost in the last 12 months")

    def get_average_cost_and_turns(self, product_ids):
        if not product_ids:
            return {}
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
                and pt.active=true
            )
            select
                a.product_id,
                (coalesce(b6.balance, 0.0) + coalesce(e.balance, 0.0)) / 2 as avg_6_balance,
                (coalesce(b12.balance, 0.0) + coalesce(e.balance, 0.0)) / 2 as avg_12_balance,
                coalesce(c6.credit, 0.0) as consumed_6_cost,
                coalesce(c12.credit, 0.0) as consumed_12_cost
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
            where a.product_id in %s
        """
        self.env.cr.execute(query, (tuple(product_ids),))
        prod_turns = {}
        for prod in self.env.cr.fetchall():
            (prod_id, avg_6_bal, avg_12_bal, cons_6m, cons_12m) = prod
            prod_turns[prod_id] = {
                'avg_cost_6m': avg_6_bal,
                'avg_cost_12m': avg_12_bal,
                'consumed_cost_6m': cons_6m,
                'consumed_cost_12m': cons_12m,
                'inventory_turns_6m': avg_6_bal and cons_6m / avg_6_bal or 0.0,
                'inventory_turns_12_m': avg_12_bal and cons_12m / avg_12_bal or 0.0,
            }
        return prod_turns

    def _compute_inventory_turn_report(self):
        prod_turns = self.get_average_cost_and_turns(self.ids)

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
            prod.total_cost = prod.qty_available * prod.standard_price
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

            turns = prod_turns.get(prod.id)
            # average inventory balance
            prod.average_cost_6m = turns and turns['avg_cost_6m']
            prod.average_cost_12m = turns and turns['avg_cost_12m']
            # Consumed Cost
            prod.consumed_cost_6m = turns and turns['consumed_cost_6m']
            prod.consumed_cost_12m = turns and turns['consumed_cost_12m']
            # Turns / Cycles per Month
            prod.inventory_turns_6m = turns and turns['inventory_turns_6m']
            prod.inventory_turns_12m = turns and turns['inventory_turns_12_m']


class ProductCategory(models.Model):
    _inherit = 'product.category'

    average_cost_6m = fields.Float(
        compute="_compute_inventory_turn_report",
        help="Average cost of inventory in the last 6 months")
    average_cost_12m = fields.Float(
        compute="_compute_inventory_turn_report",
        help="Average cost of inventory in the last 12 months")
    consumed_cost_6m = fields.Float(
        compute="_compute_inventory_turn_report",
        help="Consumed cost in the last 6 months")
    consumed_cost_12m = fields.Float(
        compute="_compute_inventory_turn_report",
        help="Consumed cost in the last 12 months")
    inventory_turns_6m = fields.Float(
        compute="_compute_inventory_turn_report",
        help="Inventory Turns / Cycles in the last 6 months")
    inventory_turns_12m = fields.Float(
        compute="_compute_inventory_turn_report",
        help="Inventory Turns / Cycles in the last 12 months")

    def get_average_cost_and_turns(self, cat_ids):
        if not cat_ids:
            return {}
        query = """
            with a as (
                select
                    pp.id as product_id,
                    pc.id as category_id,
                    aa.id as account_id
                from product_product pp
                left join product_template pt on pt.id=pp.product_tmpl_id
                left join product_category as pc on pc.id=pt.categ_id
                left join ir_property as ip
                    on ip.res_id='product.category,'||pt.categ_id
                    and ip.name='property_stock_valuation_account_id'
                left join account_account as aa
                    on 'account.account,'||aa.id=ip.value_reference
                where pt.type='product'
                and pt.active=true
            )
            select
                a.category_id,
                sum((coalesce(b6.balance, 0.0) + coalesce(e.balance, 0.0)) / 2) as avg_6_balance,
                sum((coalesce(b12.balance, 0.0) + coalesce(e.balance, 0.0)) / 2) as avg_12_balance,
                sum(coalesce(c6.credit, 0.0)) as consumed_6_cost,
                sum(coalesce(c12.credit, 0.0)) as consumed_12_cost
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
            where a.category_id in %s
            group by a.category_id
        """
        self.env.cr.execute(query, (tuple(cat_ids),))
        cat_turns = {}
        for turn_values in self.env.cr.fetchall():
            (cat_id, avg_6_bal, avg_12_bal, cons_6m, cons_12m) = turn_values
            cat_turns[cat_id] = {
                'avg_cost_6m': avg_6_bal,
                'avg_cost_12m': avg_12_bal,
                'consumed_cost_6m': cons_6m,
                'consumed_cost_12m': cons_12m,
                'inventory_turns_6m': avg_6_bal and cons_6m/avg_6_bal or 0.0,
                'inventory_turns_12_m': avg_12_bal and cons_12m/avg_12_bal or 0.0,
            }
        return cat_turns

    def _compute_inventory_turn_report(self):
        cat_turns = self.get_average_cost_and_turns(self.ids)
        for category in self:
            if not cat_turns.get(category.id):
                continue
            # average inventory balance
            category.average_cost_6m = cat_turns[category.id]['avg_cost_6m']
            category.average_cost_12m = cat_turns[category.id]['avg_cost_12m']
            # Consumed Cost
            category.consumed_cost_6m = cat_turns[category.id]['consumed_cost_6m']
            category.consumed_cost_12m = cat_turns[category.id]['consumed_cost_12m']
            # Turns / Cycles per Month
            category.inventory_turns_6m = cat_turns[category.id]['inventory_turns_6m']
            category.inventory_turns_12m = cat_turns[category.id]['inventory_turns_12_m']
