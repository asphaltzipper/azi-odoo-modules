# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProductTemplate(models.Model):
    _inherit = "product.template"

    eco_line_revision_ids = fields.One2many(
        comodel_name='ecm.eco.rev.line',
        inverse_name='product_id',
        help="ECO Line that revised this product to a later version")
    eco_line_release_ids = fields.One2many(
        comodel_name='ecm.eco.rev.line',
        inverse_name='new_product_id',
        help="ECO Line that released this version of this product")
    eco_line_intro_ids = fields.One2many(
        comodel_name='ecm.eco.intro.line',
        inverse_name='product_id',
        help="ECO Line that introduced this as a new product")
    release_eco_id = fields.Many2one(
        comodel_name='ecm.eco',
        compute='_compute_eco',
        string='Release ECO',
        readonly=True,
        store=False,
        help="ECO that released this version of this product")
    revision_eco_id = fields.Many2one(
        comodel_name='ecm.eco',
        compute='_compute_eco',
        string='Revise ECO',
        readonly=True,
        store=False,
        help="ECO that revised this product to a later version")

    @api.depends('eco_line_revision_ids', 'eco_line_release_ids', 'eco_line_intro_ids')
    def _compute_eco(self):
        for prod in self:
            # each product version can only be referenced on an ECO once
            prod.revision_eco_id = prod.eco_line_revision_ids.eco_id
            prod.release_eco_id = prod.eco_line_intro_ids.eco_id or prod.eco_line_release_ids.eco_id
