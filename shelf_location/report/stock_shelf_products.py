# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
from odoo.addons import decimal_precision as dp


class StockShelfProducts(models.Model):
    _name = 'stock.shelf.products'
    _auto = False
    _order = 'shelf_id, product_id'

    # these fields selected from the database view
    shelf_id = fields.Many2one(
        comodel_name='stock.shelf',
        string='Shelf',
        required=True)

    product_id = fields.Many2one(
        comodel_name='product.template',
        string='Product',
        required=True)

    categ_id = fields.Many2one(
        comodel_name='product.category',
        string='Category',
        required=True)

    uom_id = fields.Many2one(
        comodel_name='product.uom',
        string="UOM",
        related='product_id.uom_id')

    product_name = fields.Char(
        string='Description',
        related='product_id.name')

    # the database view gets a default code even when the product.product is not active
    default_code = fields.Char(
        string='Internal Reference',
        required=True)

    barcode = fields.Char(
        string='Barcode',
        required=True)

    deprecated = fields.Boolean(
        string='Deprecated',
        required=True)

    active = fields.Boolean(
        string='Active',
        required=True)

    # get quant data from the database view because we are gouping it
    location_qty = fields.Float(
        string='Quantity On Hand',
        digits=dp.get_precision('Product Unit of Measure'),
        required=True)

    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location',
        required=True)

    # pretend this is a stored related field so the ORM will provide the alias
    product_type = fields.Selection(
        string='Product Type',
        related='product_id.type',
        required=True,
        store=True)

    def group_shelf_products(self):
        res = {}
        # res = {
        #   shelf_id1: {
        #     'shelf': '',
        #     'products': [],
        #     'prod_count': 0,
        #   },
        #   shelf_id2: {
        for line in self:
            if res.get(line.shelf_id.id):
                res[line.shelf_id.id]['products'].append(line)
                res[line.shelf_id.id]['prod_count'] += 1
            else:
                res[line.shelf_id.id] = {'shelf': line, 'products': [line], 'prod_count': 1}
        return res.values()

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'stock_history')
        self._cr.execute("""
            CREATE OR REPLACE VIEW stock_shelf_products AS (
                select
                    -- generate a unique integer for the id
                    -- if the id exceeds 2147483647 there may be a problem with python on 32 bit systems 
                    -- shift the digits of a to the left by the number of digits in b and c
                    -- shift the digits of b to the left by the number of digits in c
                    -- then add a, b and c together
                    -- this will always be unique
                    (a*10^(b_size+c_size)+b*10^(c_size)+c)::bigint as id,
                    shelf_id,
                    product_id,
                    categ_id,
                    uom_id,
                    product_name,
                    default_code,
                    barcode,
                    deprecated,
                    active,
                    location_qty,
                    location_id,
                    product_type
                from (
                    select
                        coalesce(t.id, 0) as a,
                        coalesce(r.stock_shelf_id, 0) as b,
                        char_length((select max(id) from stock_shelf)::varchar) as b_size,
                        coalesce(q.location_id, 0) as c,
                        char_length((select max(id) from stock_location)::varchar) as c_size,
                        r.stock_shelf_id as shelf_id,
                        t.id as product_id,
                        t.categ_id,
                        t.uom_id,
                        t.name as product_name,
                        t.default_code,
                        t.barcode,
                        t.deprecated,
                        t.active,
                        q.qty as location_qty,
                        q.location_id,
                        t.type as product_type
                    from product_template_stock_shelf_rel as r
                    full outer join (
                        select
                            t.id,
                            t.type,
                            t.categ_id,
                            t.uom_id,
                            t.name,
                            bool_and(p.deprecated) as deprecated,
                            bool_and(p.active) as active,
                            array_to_string(array_agg(p.default_code), ', ') as default_code,
                            case when count(*)>1 then null else max(barcode) end as barcode
                        from product_product as p
                        left join product_template as t on t.id=p.product_tmpl_id
                        group by t.id, t.type, t.categ_id, t.uom_id, t.name
                    ) as t on t.id=r.product_template_id
                    left join (
                        select p.product_tmpl_id, q.location_id, sum(q.qty) as qty
                        from stock_quant as q
                        left join stock_location as l on l.id=q.location_id
                        left join product_product as p on p.id=q.product_id
                        where l.usage='internal'
                        group by p.product_tmpl_id, q.location_id
                    ) as q on q.product_tmpl_id=t.id
                ) as sp
            )
        """)
