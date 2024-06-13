from odoo import models, fields, api, _


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
        compute='_compute_scheduled',
        store=True,
        compute_sudo=True
    )

    scheduled_date = fields.Datetime(
        string='Scheduled Date',
        compute='_compute_scheduled',
        compute_sudo=True
    )

    @api.depends('stock_request_ids')
    def _compute_scheduled(self):
        for line in self:
            stock_request = line.stock_request_ids.filtered(lambda x: x.state in ['draft', 'submitted', 'open'])
            line.is_scheduled = len(stock_request) and True or False
            line.scheduled_date = stock_request and stock_request[0].expected_date
