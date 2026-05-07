from odoo import models, api, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    tsb_serial_ids = fields.Many2many(
        comodel_name='tsb.serial',
        relation='tsb_serial_sale_order_rel',
        column1='sale_order_id',
        column2='tsb_serial_id',
        string='TSB Serials',
    )
    tsb_bulletin_ids = fields.Many2many(
        comodel_name='tsb.bulletin',
        compute='_compute_tsb_bulletins',
        store=True,
        string='Technical Service Bulletins',
    )

    @api.depends('tsb_serial_ids.bulletin_id')
    def _compute_tsb_bulletins(self):
        for record in self:
            record.tsb_bulletin_ids = record.tsb_serial_ids.mapped('bulletin_id')


    def action_set_tsb_done(self):
        for record in self:
            record.tsb_serial_ids.write({'done_date': fields.Date.today()})