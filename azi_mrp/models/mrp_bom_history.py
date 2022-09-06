from odoo import models, api, fields


class MrpBomHistory(models.Model):
    _name = 'mrp.bom.history'
    _description = 'BOM History'

    mrp_production_id = fields.Many2one('mrp.production', 'Manufacturing Order')
    bom_history_line_ids = fields.One2many('mrp.bom.history.line', 'bom_history_id', 'BOM Lines History')
    bom_id = fields.Many2one('mrp.bom', 'Main BOM')


class MrpBomHistoryLine(models.Model):
    _name = 'mrp.bom.history.line'
    _description = 'BOM History Details'

    bom_history_id = fields.Many2one('mrp.bom.history', 'BOM History')
    product_id = fields.Many2one('product.product', 'Product')
    product_qty = fields.Float('Quantity')
    product_uom_id = fields.Many2one('uom.uom', 'Product Unit of Measure')
    sequence = fields.Integer('Sequence', default=1)
