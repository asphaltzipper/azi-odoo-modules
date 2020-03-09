from odoo import models, fields, api


class StockShelf(models.Model):
    _inherit = 'stock.shelf'

    def _find_product_from_barcode(self, barcode):
        """
        Method to be inherited and extended for finding products from alternate barcoded objects
        :param barcode: string from barcode scan
        :return: product
        """
        product = super(StockShelf, self)._find_product_from_barcode(barcode)
        if product:
            return product
        # check for scans of e-kanban barcodes
        kanban = self.env['stock.request.kanban'].with_context(active_test=False).search([('name', '=', barcode)])
        if kanban:
            return kanban.product_id
        else:
            return product
