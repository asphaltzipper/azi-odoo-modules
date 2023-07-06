# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression


class EngineeringCategory(models.Model):
    _name = 'engineering.category'
    _description = "Engineering Category"
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'

    name = fields.Char(
        string='Name',
        index=True,
        required=True,
        translate=True)
    complete_name = fields.Char(
        string='Complete Name',
        compute='_compute_complete_name',
        store=True, recursive=True)
    parent_id = fields.Many2one(
        comodel_name='engineering.category',
        string='Parent Category',
        index=True,
        ondelete='cascade')
    parent_path = fields.Char(index=True, unaccent=False)
    child_id = fields.One2many(
        comodel_name='engineering.category',
        inverse_name='parent_id',
        string='Child Categories')
    parent_left = fields.Integer(string='Left Parent', index=1)
    parent_right = fields.Integer(string='Right Parent', index=1)
    type = fields.Selection(
        selection=[('view', 'View'), ('normal', 'Normal')],
        string='Category Type', default='normal',
        help="Type 'view' is virtual, for creating a hierarchical structure.  "
             "Products cannot be assigned to this type of category.")
    product_count = fields.Integer(
        string='# Products',
        compute='_compute_product_count',
        help="The number of products under this category (Does not consider the children categories)")

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = '%s / %s' % (category.parent_id.complete_name, category.name)
            else:
                category.complete_name = category.name

    def _compute_product_count(self):
        read_group_res = self.env['product.template'].read_group([('categ_id', 'in', self.ids)], ['categ_id'], ['categ_id'])
        group_data = dict((data['categ_id'][0], data['categ_id_count']) for data in read_group_res)
        for categ in self:
            categ.product_count = group_data.get(categ.id, 0)

    @api.constrains('parent_id')
    def _check_category_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('Error ! You cannot create recursive categories.'))
        return True

    def name_get(self):
        def get_names(cat):
            """ Return the list [cat.name, cat.parent_id.name, ...] """
            res = []
            while cat:
                res.append(cat.name)
                cat = cat.parent_id
            return res
        return [(cat.id, " / ".join(reversed(get_names(cat)))) for cat in self]
