from datetime import datetime, timedelta
from openerp import api, fields, models, _

class ShelfLocation(models.Model):
    _name = 'shelf.location'
    _description = "Shelf Location"

    @api.depends('product_id')
    def location_product(self):
        prod_ids = []
        product_obj = self.env["product.template"]
        tools_obj = self.env['tools.master']
        related_recordset = product_obj.search(['|',('active', '=', False),('active', '=', True)])
        for product_rec in related_recordset:
            for loc_rec in product_rec.shelf_ids:
                if loc_rec.name == self.location_id.name:
                     prod_ids.append((4,product_rec.id))
        self.product_id = prod_ids

    @api.depends('product_id')
    def inactive_product_count(self):
        prod_ids = []
        product_obj = self.env["product.template"]
        tools_obj = self.env['tools.master']
        related_recordset = product_obj.search([('active', '=', False)])
        for product_rec in related_recordset:
            for loc_rec in product_rec.shelf_ids:
                if loc_rec.name == self.location_id.name:
                    prod_ids.append((4,product_rec.id))
        self.inactives = len(prod_ids)

    api.depends('product_id')
    def total_product_count(self):
        prod_ids = []
        product_obj = self.env["product.template"]
        tools_obj = self.env['tools.master']
        related_recordset = product_obj.search(['|',('active', '=', False),('active', '=', True)])
        for product_rec in related_recordset:
            for loc_rec in product_rec.shelf_ids:
                if loc_rec.name == self.location_id.name:
                    prod_ids.append((4,product_rec.id))
        self.product_count = len(prod_ids)

    name = fields.Char(string='Name')
    location_id = fields.Many2one('tools.master',string='Location')
    product_id = fields.One2many('product.template', 'product_id', string='Products', compute="location_product")
    inactives = fields.Integer(string='Inactives', compute='inactive_product_count')
    product_count = fields.Integer(string='Total Product', compute='total_product_count')

class ToolsMaster(models.Model):
    _name = 'tools.master'
    _description = 'Tools Master'

    name = fields.Char(string="Name")
    shelf_id = fields.Many2one('shelf.location', string='Shelf Id')

class ToolsDetail(models.Model):
    _name = 'tools.detail'
    _description = 'Tools Detail'

    name = fields.Char(string='Location')
    location_name =  fields.Many2one('tools.master', string='Location')
    product_id = fields.Many2one('product.template', string='Product')

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    location_ids = fields.One2many('tools.detail','product_id',string="Scannning Details")
    product_id = fields.Many2one('product.template', string='Product')
    shelf_ids = fields.Many2many('tools.master', 'product_tmpl_id', 'shelf_id', string='Shelves')

