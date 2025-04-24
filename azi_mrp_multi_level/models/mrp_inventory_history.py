from odoo import models, fields, api


class MrpInventoryHistory(models.Model):
    _name = 'mrp.inventory.history'
    _description = 'MRP Multi Level History'

    product_mrp_area_id = fields.Many2one('product.mrp.area', 'Product Parameters', index=True, ondelete="cascade",)
    date = fields.Date()
    bucket = fields.Selection([('week1', 'Week 1'), ('week2', 'Week 2'), ('week3', 'Week 3')], 'Bucket')
    supply_method = fields.Selection([('buy', 'Buy'), ('none', 'Undefined'), ('manufacture', 'Produce'),
                                      ('phantom', 'Kit'), ('pull', 'Pull From'), ('push', 'Push To'),
                                      ('pull_push', 'Pull & Push')], 'Supply Method')
    to_expedite = fields.Boolean('Expedite')
    on_blanket = fields.Boolean('Blanket')
    e_kanban = fields.Boolean('E-Kanban')
    kit_qty = fields.Integer('Kits')
    routing_name = fields.Char('Work Routing')
    deprecated = fields.Boolean('Obsolete')
    to_procure = fields.Float('Procure Qty')
    order_count = fields.Integer('Order Count', compute='_compute_order_count')

    @api.depends('product_mrp_area_id')
    def _compute_order_count(self):
        for record in self:
            record.order_count = self.search_count([('product_mrp_area_id', '=', record.product_mrp_area_id.id)])
