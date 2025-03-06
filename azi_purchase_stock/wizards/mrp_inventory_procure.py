from odoo import api, models, tools, _


class MrpInventoryProcure(models.TransientModel):
    _inherit = 'mrp.inventory.procure'

    def make_procurement(self):
        return super(MrpInventoryProcure, self.with_context(procure_wizard=True)).make_procurement()
