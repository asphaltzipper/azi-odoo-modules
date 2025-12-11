from odoo import models, fields


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    reconfigure = fields.Boolean(
        related="bom_id.reconfigure",
        string="Reconfigure",
    )

    def _is_finished_sn_already_produced(self, lot, excluded_sml=None):
        duplicates = super(MrpProduction, self)._is_finished_sn_already_produced(lot, excluded_sml)
        if not duplicates:
            return False
        # since we are pulling this serial from production, check if its latest move
        # places it in production
        domain = [
            ('lot_id', '=', lot.id),
            ('qty_done', '=', 1),
            ('state', '=', 'done'),
        ]
        latest_move = self.env['stock.move.line'].search(domain, order='date desc', limit=1)
        if latest_move.location_dest_id.usage == 'production' and self.reconfigure:
            return False
        return True
