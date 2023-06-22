from odoo import fields, models, _


class WizardShelfProductScan(models.TransientModel):
    _name = "wizard.shelf.product.scan"
    _inherit = 'barcodes.barcode_events_mixin'

    shelf_id = fields.Many2one(
        comodel_name='stock.shelf',
        readonly=True,
    )
    product_tmpl_id = fields.Many2one(
        'product.template',
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
        return self.env['product.template'].with_context(active_test=False).search(
            ['|', ('barcode', '=', barcode), ('default_code', '=', barcode)])

    def on_barcode_scanned(self, barcode):
        # TODO: add code to switch shelf when a shelf name is scanned
        self.product_tmpl_id = self.search_product_barcode(barcode)
        if self.product_tmpl_id:
            self.status_state = 0
            self.shelf_id.write({
                'product_ids': [(4, self.product_tmpl_id.id)]
            })
        else:
            self.status = _("Barcode %s does not correspond to any "
                            "product. Try with another barcode or "
                            "press Close to finish scanning.") % barcode
            self.status_state = 1
            self.env.user.notify_warning(message=barcode, title="Unknown Barcode", sticky=True)
