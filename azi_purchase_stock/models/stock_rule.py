from odoo import models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _prepare_purchase_order(self, product_id, product_qty, product_uom, origin, values, partner):
        res = super(StockRule, self)._prepare_purchase_order(product_id, product_qty, product_uom, origin, values, partner)
        procure_wizard = self.env.context.get('procure_wizard', False)
        user_id = self.env.context.get('uid', False)
        if procure_wizard and user_id:
            res['user_id'] = user_id
        return res
