from odoo import tools
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class AttributeValueProductsReport(models.Model):
    _name = "attribute.value.products.report"
    _description = "Attribute Value Products Report"
    _auto = False
    _order = 'product_attribute_id, product_attribute_value_id'

    product_tmpl_id = fields.Many2one(
        comodel_name='product.template')
    product_attribute_id = fields.Many2one(
        comodel_name='product.attribute',
        string='Attribute')
    product_attribute_value_id = fields.Many2one(
        comodel_name='product.attribute.value',
        string='Value')
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Component')
    product_qty = fields.Float(
        string='Quantity',
        digits=dp.get_precision('Unit of Measure'))

    def _query(self):
        select = """
            select
                coalesce(
                        tv.product_attribute_value_id,
                        bv.product_attribute_value_id
                    ) as id,
                t.id as product_tmpl_id,
                tv.product_attribute_id,
                coalesce(
                        tv.product_attribute_value_id,
                        bv.product_attribute_value_id
                    ) as product_attribute_value_id,
                bv.product_id,
                bv.product_qty
            from product_template as t
            left join (
                -- template attribute values
                select
                    tl.product_tmpl_id,
                    tl.attribute_id as product_attribute_id,
                    tr.product_attribute_value_id
                from product_attribute_value_product_template_attribute_line_rel as tr
                left join product_template_attribute_line as tl
                    on tl.id=product_template_attribute_line_id
            ) as tv on tv.product_tmpl_id=t.id
            full outer join (
                -- config bom line attribute values
                select
                    b.product_tmpl_id,
                    l.bom_id,
                    l.product_id,
                    l.product_qty,
                    r.product_attribute_value_id,
                    v.attribute_id as product_attribute_id
                from mrp_bom as b
                left join mrp_bom_line as l on l.bom_id=b.id
                left join mrp_bom_line_product_attribute_value_rel as r
                    on r.mrp_bom_line_id=l.id
                left join product_attribute_value as v
                    on v.id=r.product_attribute_value_id
                where b.product_id is null
            ) as bv on
                bv.product_tmpl_id=t.id
                and bv.product_attribute_value_id=tv.product_attribute_value_id
            where t.config_ok=true
            order by 
                t.id,
                coalesce(tv.product_attribute_id,
                    bv.product_attribute_id),
                coalesce(tv.product_attribute_value_id,
                    bv.product_attribute_value_id),
                bv.bom_id
        """
        return select

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (
            self._table, self._query()))
