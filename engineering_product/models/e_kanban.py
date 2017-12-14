from odoo import api, models, fields


class EKanbanBatchLine(models.Model):
    _inherit = "stock.e_kanban_batch.line"

    deprecated = fields.Boolean(
        string='Deprecated',
        related='product_id.deprecated',
        readonly=True,
        store=True)
