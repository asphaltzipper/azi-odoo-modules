from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    stock_request_ids = fields.One2many(
        comodel_name='stock.request',
        inverse_name='sale_order_line_id',
        string='Stock Requests',
        readonly=True,
    )

    is_scheduled = fields.Boolean(
        string='Scheduled',
        compute='_compute_is_scheduled',
        store=True,
    )

    @api.depends('stock_request_ids')
    def _compute_is_scheduled(self):
        for line in self:
            line.is_scheduled = line.stock_request_ids and\
                                line.stock_request_ids.filtered(lambda x: x.state in ['draft', 'submitted', 'open']) or\
                                False
