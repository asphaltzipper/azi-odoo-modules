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
            if record.type == 'add':
                move_lines = record.lot_id.move_line_ids.filtered(lambda l: l.move_id.production_id)
                if move_lines:
                    record.has_child = True
                else:
                    record.has_child = self.env['mrp.bom'].search([('product_id', '=', record.product_id.id)])\
                                       and True or False