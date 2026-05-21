from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Repair(models.Model):
    _inherit = 'repair.order'

    tsb_serial_ids = fields.Many2many(
        comodel_name='tsb.serial',
        relation='tsb_serial_repair_order_rel',
        column1='repair_order_id',
        column2='tsb_serial_id',
        compute='_compute_tsb_serials',
        store=True,
        readonly=True,
        string='TSB Serials',
    )
    tsb_bulletin_ids = fields.Many2many(
        comodel_name='tsb.bulletin',
        string='Technical Service Bulletins',
        help='Select one or more TSBs for the Lot/Serial being repaired',
    )

    @api.depends('lot_id', 'tsb_bulletin_ids')
    def _compute_tsb_serials(self):
        tsb_serials = self.env['tsb.serial'].search([
            ('bulletin_id', 'in', self.tsb_bulletin_ids.ids),
            ('lot_id', 'in', self.lot_id.ids),
        ])
        for rec in self:
            rec.tsb_serial_ids = tsb_serials.filtered(lambda x: x.bulletin_id in rec.tsb_bulletin_ids and x.lot_id == rec.lot_id)

    def action_set_tsb_done(self):
        for record in self:
            if not record.tsb_serial_ids:
                raise UserError(_("%s is missing TSB Serials", record.name))
            record.tsb_serial_ids.write({'done_date': fields.Date.today()})
