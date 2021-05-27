from odoo import models, api, _


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.onchange('product_id', 'picking_id.picking_type_code')
    def onchange_product_id_warning(self):
        if not self.product_id:
            return
        warning = {}
        title = False
        message = False
        product_info = self.product_id
        if self.picking_id.picking_type_code == 'outgoing' and product_info.receipt_line_warn != 'no-message':
            title = _("Warning for %s") % product_info.name
            message = product_info.receipt_line_warn_msg
            warning['title'] = title
            warning['message'] = message
            if product_info.receipt_line_warn == 'block':
                self.product_id = False
            return {'warning': warning}
        return {}
