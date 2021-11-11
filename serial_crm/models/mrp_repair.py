from odoo import fields, models, api


class Repair(models.Model):
    _inherit = 'repair.order'

    move_date = fields.Datetime(
        string="Move Date",
        related='move_id.date',
        readonly=True,
        store=True)


class RepairLine(models.Model):
    _inherit = 'repair.line'

    has_child = fields.Boolean(string='Has Child', compute='_compute_has_child', store=True)

    @api.depends('lot_id.repair_ids.operations')
    def _compute_has_child(self):
        for record in self:
            record.has_child = (record.type == 'add' and record.lot_id.mapped('repair_ids.operations')) \
                               and True or False

