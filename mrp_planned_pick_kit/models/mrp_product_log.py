from odoo import models, fields, api, _


class MRPProductLog(models.Model):
    _name = 'mrp.product.log'
    _description = 'MRP Product Log'
    _order = 'create_date DESC'

    message = fields.Char('Message')
    type = fields.Selection([('info', 'Info'), ('make', 'Make Kit'), ('other', 'Other')],
                            default='info')
    product_id = fields.Many2one('product.product')
