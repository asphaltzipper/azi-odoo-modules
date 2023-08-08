# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

import re


class ProductCategory(models.Model):
    _inherit = "product.category"

    # products managed by engineering (used in production) should always have a valid default_code
    eng_management = fields.Boolean(
        string="Engineering Management",
        default=False,
        help="Products in this category are under engineering management.  "
             "They will require a valid Internal Reference code.")
    eng_code_sequence = fields.Many2one(
        string="Engineering Code Sequence",
        comodel_name="ir.sequence",
        help="Products created in this category will receive an engineering code from this sequence")
    default_rev = fields.Char(string="Default Revision")
    rev_delimiter = fields.Char(string="Revision Delimiter")
    def_code_regex = fields.Char(
        string="Product Code RegEx",
        help="Regular Expression to be used when validating product's Internal Reference.  "
             "Leave this field empty to accept any code format.")

    @api.constrains('eng_management', 'eng_code_sequence', 'default_rev', 'rev_delimiter', 'def_code_regex')
    def _validate_eng_management(self):
        if self.eng_management:
            if not self.eng_code_sequence or not self.default_rev or not self.rev_delimiter:
                raise ValidationError("With Engineering Management enabled, all management parameters are required")


class ProductTemplate(models.Model):
    _inherit = "product.template"

    eng_management = fields.Boolean(related='categ_id.eng_management', readonly="1")
    rev_delimiter = fields.Char(related='categ_id.rev_delimiter', readonly="1")
    eng_code = fields.Char(
        string='Engineering Code',
        compute='_compute_eng_code',
        readonly=True,
        store=True)
    eng_rev = fields.Char(
        string='Engineering Revision',
        compute='_compute_eng_code',
        readonly=True,
        store=True)
    eng_categ_id = fields.Many2one(
        comodel_name='engineering.category',
        string='Engineering Category',
        domain="[('type','=','normal')]",
        copy=True,
        help="Select category for the current product")
    eng_type_id = fields.Many2one(
        related='product_variant_ids.eng_type_id')
    eng_mod_flag = fields.Boolean(
        related='product_variant_ids.eng_mod_flag',
        readonly=False)
    eng_hold_flag = fields.Boolean(
        related='product_variant_ids.eng_hold_flag',
        readonly=False)
    deprecated = fields.Boolean(
        string='Deprecated',
        compute='_compute_deprecated',
        inverse='_set_deprecated',
        store=True,
        index=True)
    eng_notes = fields.Text(
        string='Engineering Notes',
        compute='_compute_eng_notes',
        inverse='_set_eng_notes')
    preparation_id = fields.Many2one(
        comodel_name='engineering.preparation',
        string='Prep')
    coating_id = fields.Many2one(
        comodel_name='engineering.coating',
        string='Coating')
    make = fields.Selection(
        selection=[
            ('P', 'Purchase'),
            ('M', 'Manufacture'),
        ],
        string='Make',
        compute='_compute_make',
        help="Selected production routes include manufacturing (M) or not (P)")
    doc_ids = fields.One2many(
        comodel_name='ir.attachment',
        inverse_name='res_id',
        domain=[('res_model', '=', 'product.template'), ('type', '=', 'binary')],
        readonly=True,
        string='Documents')
    version_ids = fields.One2many(
        comodel_name='product.template',
        string='Other Versions',
        compute='_compute_version_ids')
    version_doc_ids = fields.One2many(
        comodel_name='ir.attachment',
        string='Version Documents',
        readonly=True,
        compute='_compute_version_doc_ids')

    @api.depends('route_ids')
    def _compute_make(self):
        for prod in self:
            rules = prod.route_ids.mapped('rule_ids')
            actions = rules and rules.mapped('action') or []
            prod.make = 'manufacture' in actions and 'M' or 'P'

    @api.depends('categ_id', 'product_variant_ids', 'product_variant_ids.default_code')
    def _compute_version_ids(self):
        for prod in self:
            if prod.eng_management:
                domain = [
                    # ('id', '!=', prod.id),
                    ('eng_management', '=', True),
                    ('eng_code', '=', prod.eng_code),
                    '|', ('active', '=', True), ('active', '=', False)]
                versions = prod.search(domain, order='default_code')
                prod.version_ids = versions.ids
            else:
                prod.version_ids = None

    @api.depends('categ_id', 'product_variant_ids', 'product_variant_ids.default_code')
    def _compute_version_doc_ids(self):
        for prod in self:
            if prod.eng_management:
                vers_domain = [
                    # ('id', '!=', prod.id),
                    ('eng_management', '=', True),
                    ('eng_code', '=', prod.eng_code),
                    '|', ('active', '=', True), ('active', '=', False)]
                versions = prod.search(vers_domain)
                doc_domain = [('res_model', '=', 'product.template'), ('res_id', 'in', versions.ids)]
                prod.version_doc_ids = self.env['ir.attachment'].search(doc_domain)
            else:
                prod.version_doc_ids = None

    @api.constrains('eng_categ_id')
    def _validate_eng_cat(self):
        if self.eng_management:
            if not self.eng_categ_id:
                raise ValidationError("Engineering Category is required for this Product Category")
        return True

    @api.constrains('name')
    def _validate_name_chars(self):
        if self.name:
            invalid_chars = [" ", ".", "\t"]
            if self.name[-1] in invalid_chars or self.name[0] in invalid_chars:
                raise ValidationError("Product names can't begin or end with dots, spaces, or tabs")
        return True

    @api.depends('categ_id', 'product_variant_ids', 'product_variant_ids.default_code')
    def _compute_eng_code(self):
        unique_variants = self.filtered(lambda x: len(x.product_variant_ids) == 1 and x.categ_id.eng_management)
        for tmpl in unique_variants:
            tmpl.eng_code, tmpl.eng_rev = tmpl.product_variant_ids._parse_default_code(
                tmpl.product_variant_ids.default_code,
                tmpl.categ_id.def_code_regex
            )
        for tmpl in (self - unique_variants):
            tmpl.eng_code, tmpl.eng_rev = ('', '')

    @api.depends('product_variant_ids', 'product_variant_ids.deprecated')
    def _compute_deprecated(self):
        for tmpl in self:
            tmpl.deprecated = all([x.deprecated for x in tmpl.product_variant_ids])

    def _set_deprecated(self):
        for variant in self.product_variant_ids:
            variant.deprecated = self.deprecated

    @api.depends('product_variant_ids', 'product_variant_ids.eng_notes')
    def _compute_eng_notes(self):
        unique_variants = self.filtered(lambda x: len(x.product_variant_ids) == 1)
        for tmpl in unique_variants:
            tmpl.eng_notes = tmpl.product_variant_ids.eng_notes
        for tmpl in (self - unique_variants):
            tmpl.eng_notes = ''

    def _set_eng_notes(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.eng_notes = self.eng_notes

    def button_revise(self, values=None):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.button_revise(values)

    def action_open_product_version(self):
        self.ensure_one()
        action = self.env.ref('engineering_product.product_template_action_one').read()[0]
        action['res_id'] = self.id
        return action


class ProductProduct(models.Model):
    _inherit = "product.product"

    _sql_constraints = [('default_code_uniq', 'unique (default_code)', "Product Code must be unique."), ]

    eng_code = fields.Char(
        string="Engineering Code",
        compute='_compute_eng_code',
        readonly=True,
        store=True)
    eng_rev = fields.Char(
        string="Engineering Revision",
        compute='_compute_eng_code',
        readonly=True,
        store=True)
    eng_type_id = fields.Many2one(
        comodel_name='engineering.part.type',
        string='Eng Type',
        copy=True,
        help="Engineering part type")
    eng_mod_flag = fields.Boolean(
        string="No-ECO Modification",
        tracking=True,
        copy=False,
        help="Part changed with no ECO or revision")
    eng_hold_flag = fields.Boolean(
        string="Hold Production",
        tracking=True,
        copy=False,
        help="A revision is impending, stop producing/purchasing this part")
    deprecated = fields.Boolean(
        string='Deprecated',
        default=False,
        required=True,
        copy=False,
        index=True)
    eng_notes = fields.Text('Engineering Notes')

    @api.depends('product_tmpl_id.categ_id', 'default_code')
    def _compute_eng_code(self):
        for prod in self:
            if prod.product_tmpl_id.categ_id.eng_management:
                prod.eng_code, prod.eng_rev = prod._parse_default_code(
                    prod.default_code,
                    prod.product_tmpl_id.categ_id.def_code_regex
                )

    def _parse_default_code(self, default_code, def_code_regex):
        code_match = re.match(def_code_regex, default_code or '')
        res = code_match and (code_match.group(1), code_match.group(2)) or (False, False)
        return res

    @api.constrains('default_code', 'product_tmpl_id')
    def _validate_default_code(self):
        category = self.product_tmpl_id.categ_id
        if category.eng_management:
            if not self.default_code:
                raise ValidationError("Internal Reference code is required for this Engineering Category")
            if category.def_code_regex and not re.match(category.def_code_regex, self.default_code):
                raise ValidationError("Internal Reference code is not valid for this Engineering Category")
        return True

    @api.model
    def create(self, vals):
        if not (vals.get('eng_code') and vals.get('eng_rev')):
            cat = vals.get('categ_id') and self.env['product.category'].browse(vals['categ_id'])
            if not cat:
                tmpl = self.env['product.template'].browse(vals.get('product_tmpl_id'))
                cat = tmpl.categ_id
            if cat and cat.eng_management:
                if not vals.get('default_code'):
                    vals['default_code'] = "%s%s%s" % (
                        cat.eng_code_sequence.next_by_id(),
                        cat.rev_delimiter,
                        cat.default_rev,
                    )
        product = super(ProductProduct, self.with_context(create_product_product=True)).create(vals)
        return product

    def write(self, values):
        if 'default_code' not in values.keys():
            # the user is not changing the default code, so we assume it still passes requirements
            pass
        elif not values.get('default_code'):
            # the user is deleting the default code, so get the next in sequence
            cat = self.env['product.category'].browse(values.get('categ_id', self.categ_id.id))
            if cat.eng_management:
                values['default_code'] = "%s%s%s" % (
                    cat.eng_code_sequence.next_by_id(),
                    cat.rev_delimiter,
                    cat.default_rev,
                )
        res = super(ProductProduct, self).write(values)
        return res

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if self._context.get('search_default_eng_categ_id'):
            args.append(('eng_categ_id', 'child_of', self._context['search_default_eng_categ_id']))
        return super(ProductProduct, self).search(args, offset=offset, limit=limit, order=order, count=count)

    # TODO: create a revision wizard
    def button_revise(self, values=None):
        """
        Best if called by a wizard where the user can specify a new rev
        Revisions are only allowed for non-configurable products.
        """
        self.ensure_one()
        if values is None:
            values = {}

        if self.product_tmpl_id.attribute_line_ids \
                or self.product_tmpl_id.product_variant_count > 1:
            raise UserError(
                _("Can't revise this product because it's a variant of "
                  "configurable product %s" % (self.product_tmpl_id.name, ))
            )

        if not self.eng_code:
            raise UserError(_('Please set the `engineering code`'))
        # copy product
        defaults = {
            'name': self.name,
            'default_code':
                self.eng_code + self.product_tmpl_id.rev_delimiter + 'Z9',
        }
        defaults.update(values)
        defaults['barcode'] = defaults['default_code']
        new_prod = self.copy(default=defaults)

        # copy orderpoints
        old_ops = self.env['stock.warehouse.orderpoint'].search(
            [('product_id', '=', self.id)]
        )
        for op in old_ops:
            op.copy(default={'product_id': new_prod.id})

        # copy boms
        old_boms = self.env['mrp.bom'].search([
            '|',
            ('product_tmpl_id', '=', self.product_tmpl_id.id),
            ('product_id', '=', self.id),
        ])
        for bom in old_boms:
            # unless configurable, we want product_id on mrp.bom
            defaults = {
                'product_tmpl_id': new_prod.product_tmpl_id.id,
                'product_id': new_prod.id,
            }
            bom.copy(default=defaults)

        # copy sellers
        defaults = {'product_tmpl_id': new_prod.product_tmpl_id.id}
        domain = [('product_tmpl_id', '=', self.product_tmpl_id.id)]
        if self.product_tmpl_id.product_variant_count > 1:
            # we never execute this code because of the test above
            # this only is here for future reference
            defaults['product_id'] = new_prod.id
            domain.append(('product_id', '=', self.id))
        old_sellers = self.env['product.supplierinfo'].search(domain)
        for seller in old_sellers:
            seller.copy(default=defaults)

        # deprecate and set warnings on old revision
        self.deprecated = True
        self.purchase_line_warn = 'warning'
        self.purchase_line_warn_msg = 'This product has been revised'

        return new_prod.id
