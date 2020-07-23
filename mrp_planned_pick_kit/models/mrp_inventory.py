from odoo import models, fields, api


class MrpInventory(models.Model):
    _inherit = 'mrp.inventory'

    kit_qty = fields.Integer(
        string="Kits",
        related='product_id.mfg_kit_qty',
    )

    @api.multi
    def action_create_mfg_kit(self):
        self.ensure_one()
        return self.product_id.create_mfg_kit(self.to_procure)
