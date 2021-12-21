from datetime import date
from odoo import fields, models, _


class WizardStockRequestOrderKanbanAbstract(models.AbstractModel):
    _inherit = "wizard.stock.request.kanban.abstract"

    def barcode_ending(self):
        super().barcode_ending()
        self.kanban_id.write({'verify_date': date.today()})
