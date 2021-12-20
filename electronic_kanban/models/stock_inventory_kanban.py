from odoo import api, models, fields


class StockInventoryKanban(models.Model):
    _inherit = 'stock.inventory.kanban'

    product_ids = fields.Many2many(
        'product.product', string='Products',
        domain=[('type', 'in', ['product', 'consu'])],
        ondelete='cascade',
        readonly=True, states={'draft': [('readonly', False)]},
    )
    unconfigured_product_ids = fields.Many2many(
        comodel_name='product.product',
        readonly=True,
        compute='_compute_unconfigured_product'
    )
    count_unconfigured_products = fields.Integer(
        string='Un-Configured Products',
        readonly=True,
        compute='_compute_unconfigured_product',
    )

    @api.depends('product_ids')
    def _compute_unconfigured_product(self):
        for rec in self:
            rec.unconfigured_product_ids = rec.product_ids.filtered(
                lambda r: not r.e_kanban_verified
            )
            rec.count_unconfigured_products = len(rec.unconfigured_product_ids)

    @api.multi
    def print_missing_kanbans_2x1(self):
        """ Print the missing kanban cards in order to restore them
        """
        self.ensure_one()
        return self.env.ref(
            'azi_stock_request_kanban.action_report_kanban_label_2x1').report_action(
            self.missing_kanban_ids
        )
