from odoo import fields, models, _


class WizardShelfProductScan(models.TransientModel):
    _inherit = "wizard.shelf.product.scan"

    def search_product_barcode(self, barcode):
        """
        Extend barcode search to include product by kanban
        """
        product = super(WizardShelfProductScan, self).\
            search_product_barcode(barcode)
        if not product:
            kanban = self.env['stock.request.kanban'].search([
                ('name', '=', barcode)
            ])
            if kanban:
                product = kanban.product_id.product_tmpl_id
        return product
