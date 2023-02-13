# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools
from odoo.tools import pycompat
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    categ_id = fields.Many2one(track_visibility='onchange')

    image_medium_big = fields.Binary(
        "Medium-big-sized image", attachment=True,
        help="Medium-big-sized image of the product. It is automatically "
             "resized as a 320x320px image, with aspect ratio preserved, "
             "only when the image exceeds one of those sizes. Use this field "
             "in form views or some kanban views.")

    @api.model
    def create(self, vals):
        image = vals.get(
            'image', vals.get(
                'image_medium_big', vals.get(
                    'image_medium', vals.get(
                        'image_small')
                )
            )
        )
        if image:
            if not vals.get('image'):
                vals['image'] = image
            if isinstance(image, pycompat.text_type):
                image = image.encode('ascii')
            vals['image_medium_big'] = tools.image_resize_image(
                image,
                size=(320, 320),
                avoid_if_small=True)
        template = super(ProductTemplate, self).create(vals)
        return template

    @api.multi
    def write(self, vals):
        image = vals.get(
            'image', vals.get(
                'image_medium_big', vals.get(
                    'image_medium', vals.get(
                        'image_small', None)
                )
            )
        )
        if image:
            if not vals.get('image'):
                vals['image'] = image
            if isinstance(image, pycompat.text_type):
                image = image.encode('ascii')
            vals['image_medium_big'] = tools.image_resize_image(
                image,
                size=(320, 320),
                avoid_if_small=True)
        if image == False:
            vals['image'] = False

        if vals['categ_id']:
            if vals['categ_id'] != self.categ_id.id and self.env.user.id != 1:
                raise ValidationError("Only the administrator can change product category")

        res = super(ProductTemplate, self).write(vals)
        return res


class ProductProduct(models.Model):
    _inherit = "product.product"

    image_medium_big = fields.Binary(
        "Medium-big-sized image",
        compute='_compute_med_big_image',
        inverse='_set_image_medium_big',
        help="Image of the product variant at 320px "
             "(Image of product template if false).")

    @api.depends('image_variant', 'product_tmpl_id.image')
    def _compute_med_big_image(self):
        for prod in self:
            if prod._context.get('bin_size'):
                prod.image_medium_big = prod.image_variant
            else:
                image = prod.image_variant
                if isinstance(image, pycompat.text_type):
                    image = image.encode('ascii')
                resized_image = tools.image_resize_image(
                    image,
                    size=(320, 320),
                    avoid_if_small=True)
                prod.image_medium_big = resized_image
            if not prod.image_medium_big:
                prod.image_medium_big = prod.product_tmpl_id.image_medium_big

    def _set_image_medium_big(self):
        self._set_image_value(self.image_medium_big)


class ProductAttributevalue(models.Model):
    _inherit = "product.attribute.value"

    @api.multi
    def _variant_name(self, variable_attributes):
        return ", ".join([
            "%s: %s" % (v.attribute_id.name, v.name)
            for v in self.sorted(key=lambda r: r.attribute_id.name)
            if v.attribute_id in variable_attributes
        ])
