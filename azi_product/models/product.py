# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools
from odoo.tools import pycompat
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    categ_id = fields.Many2one(tracking=True)
    image_medium_big = fields.Image("Medium-big-sized image", related="image_1920", max_width=320, max_height=320,
                                    store=True, help="Medium-big-sized image of the product. It is automatically "
                                    "resized as a 320x320px image, with aspect ratio preserved, "
                                    "only when the image exceeds one of those sizes. Use this field "
                                    "in form views or some kanban views.")

    def write(self, vals):
        if vals.get('categ_id') and vals['categ_id'] != self.categ_id.id and \
                self.env.user.id != self.env.ref('base.user_admin').id:
            raise ValidationError("Only the administrator can change product category")
        res = super(ProductTemplate, self).write(vals)
        if 'image_1920' in vals:
            self.env['product.product'].invalidate_model([
                'image_medium_big',
                'image_1024',
                'image_512',
                'image_256',
                'image_128',
                'can_image_1024_be_zoomed',
            ])
        return res


class ProductProduct(models.Model):
    _inherit = "product.product"

    image_variant_320 = fields.Image("Variant Image 320", related="image_variant_1920", max_width=320, max_height=320,
                                     store=True)
    image_medium_big = fields.Image("Medium-big-sized image", compute='_compute_image_320')

    def _compute_image_320(self):
        for record in self:
            record.image_medium_big = record.image_variant_320 or record.product_tmpl_id.image_medium_big

    def name_get(self):
        # TDE: this could be cleaned a bit I think

        def _name_get(d):
            name = d.get('name', '')
            code = self._context.get('display_default_code', True) and d.get('default_code', False) or False
            if code:
                name = '[%s] %s' % (code,name)
            return (d['id'], name)

        partner_id = self._context.get('partner_id')
        if partner_id:
            partner_ids = [partner_id, self.env['res.partner'].browse(partner_id).commercial_partner_id.id]
        else:
            partner_ids = []
        company_id = self.env.context.get('company_id')

        # all user don't have access to seller and partner
        # check access and use superuser
        self.check_access_rights("read")
        self.check_access_rule("read")

        result = []

        # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
        # Use `load=False` to not call `name_get` for the `product_tmpl_id`
        self.sudo().read(['name', 'default_code', 'product_tmpl_id'], load=False)

        product_template_ids = self.sudo().mapped('product_tmpl_id').ids

        if partner_ids:
            supplier_info = self.env['product.supplierinfo'].sudo().search([
                ('product_tmpl_id', 'in', product_template_ids),
                ('partner_id', 'in', partner_ids),
            ])
            # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
            # Use `load=False` to not call `name_get` for the `product_tmpl_id` and `product_id`
            supplier_info.sudo().read(['product_tmpl_id', 'product_id', 'product_name', 'product_code'], load=False)
            supplier_info_by_template = {}
            for r in supplier_info:
                supplier_info_by_template.setdefault(r.product_tmpl_id, []).append(r)
        for product in self.sudo():
            # Modify name based on variant
            product_attributes = product.product_template_attribute_value_ids.sorted(key=lambda r: r.attribute_id.name)
            variant_name = ", ".join(["%s: %s" % (attr_value.attribute_id.name, attr_value.name) for attr_value in product_attributes])
            variant = product.product_template_attribute_value_ids._get_combination_name()
            name = (product_attributes and variant_name) and "%s (%s)" % (product.name, variant_name) or product.name
            sellers = self.env['product.supplierinfo'].sudo().browse(self.env.context.get('seller_id')) or []
            if not sellers and partner_ids:
                product_supplier_info = supplier_info_by_template.get(product.product_tmpl_id, [])
                sellers = [x for x in product_supplier_info if x.product_id and x.product_id == product]
                if not sellers:
                    sellers = [x for x in product_supplier_info if not x.product_id]
                # Filter out sellers based on the company. This is done afterwards for a better
                # code readability. At this point, only a few sellers should remain, so it should
                # not be a performance issue.
                if company_id:
                    sellers = [x for x in sellers if x.company_id.id in [company_id, False]]
            if sellers:
                for s in sellers:
                    seller_variant = s.product_name and (
                        variant and "%s (%s)" % (s.product_name, variant) or s.product_name
                        ) or False
                    mydict = {
                              'id': product.id,
                              'name': seller_variant or name,
                              'default_code': s.product_code or product.default_code,
                              }
                    temp = _name_get(mydict)
                    if temp not in result:
                        result.append(temp)
            else:
                mydict = {
                          'id': product.id,
                          'name': name,
                          'default_code': product.default_code,
                          }
                result.append(_name_get(mydict))
        return result
