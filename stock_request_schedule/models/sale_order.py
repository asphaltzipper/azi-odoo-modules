from odoo import models, fields, api, _


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    stock_request_ids = fields.One2many(
        comodel_name='stock.request',
        inverse_name='sale_order_line_id',
        string='Stock Requests',
        readonly=True,
    )

    is_on_sr = fields.Boolean(
        string='On Stock Request',
        compute='_compute_scheduled',
        store=True,
        compute_sudo=True
    )

    sr_date = fields.Datetime(
        string='Stock Request Date',
        compute='_compute_scheduled',
        compute_sudo=True
    )

    @api.depends('stock_request_ids')
    def _compute_scheduled(self):
        for line in self:
            stock_request = line.stock_request_ids.filtered(lambda x: x.state in ['draft', 'submitted', 'open'])
            line.is_on_sr = len(stock_request) and True or False
            line.sr_date = stock_request and stock_request[0].expected_date or False
