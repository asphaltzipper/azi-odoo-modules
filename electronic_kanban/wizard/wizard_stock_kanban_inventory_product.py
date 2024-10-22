from odoo import fields, models, _


class WizardStockKanbanInventoryProduct(models.TransientModel):
    _name = "wizard.stock.kanban.inventory.product"
    _description = "Kanban Inventory Wizard by Barcode"
    _inherit = ['barcodes.barcode_events_mixin']

    kanban_inventory_id = fields.Many2one(
        comodel_name='stock.inventory.kanban',
        readonly=True,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        readonly=True,
    )
    status = fields.Text(
        readonly=True,
        default="Start scanning",
    )
    status_state = fields.Integer(
        default=0,
        readonly=True,
    )

    def search_product_barcode(self, barcode):
        """
        Method to be inherited and extended for finding products from alternate barcoded objects
        :param barcode: string from barcode scan
        :return: product
        """
        return self.env['product.product'].with_context(active_test=False).search(
            ['|', ('barcode', '=', barcode), ('default_code', '=', barcode)])

    def on_barcode_scanned(self, barcode):
        self.product_id = self.search_product_barcode(barcode)
        if self.product_id:
            self.status_state = 0
            self.kanban_inventory_id.write({
                'product_ids': [(4, self.product_id.id)]
            })
        else:
            self.status = _(
                "Barcode %s does not correspond to any product. Try with another "
                "barcode or press Close to finish scanning.",
                barcode,
            )
            self.status_state = 1
            self.env.user.notify_warning(message=barcode, title="Unknown Barcode", sticky=True)
