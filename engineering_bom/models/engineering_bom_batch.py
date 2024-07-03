# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools import float_compare
from odoo.exceptions import ValidationError, UserError


class EngBomBatch(models.Model):
    _name = 'engineering.bom.batch'
    _inherit = ['mail.thread']
    _description = 'Engineering BOM Batch'
    _order = 'create_date desc'

    name = fields.Char(
        string='Name',
        required=True)
    notes = fields.Text(
        string='Notes',
        required=True)
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('imported', 'Imported'),
            ('converted', 'Converted'),
            ('comparing', 'Comparing'),
            ('done', 'Done'),
            ('cancel', 'Canceled'),
        ],
        string='State',
        default='draft',
        required=True,
        track_visibility='onchange')
    owner_id = fields.Many2one(
        comodel_name='res.users',
        string="Owner",
        required=True)
    configurator_ids = fields.Many2many(
        comodel_name='product.template',
        string="Configurators",
        domain=[('config_ok', '=', True)])
    option_component_ids = fields.Many2many(
        comodel_name='product.product',
        string='Option Components',
        ondelete='cascade',
        help="Products in this batch to be split out and used as configurable option components")
    comp_ids = fields.One2many(
        comodel_name='engineering.bom.component',
        inverse_name='batch_id',
        readonly=True)
    adjacency_ids = fields.One2many(
        comodel_name='engineering.bom.adjacency',
        inverse_name='batch_id',
        readonly=True)
    eng_bom_ids = fields.One2many(
        comodel_name='engineering.bom',
        inverse_name='batch_id',
        readonly=True)
    part_diff_ids = fields.One2many(
        comodel_name='engineering.part.diff',
        inverse_name='batch_id',
        readonly=True)
    bom_diff_ids = fields.One2many(
        comodel_name='engineering.bom.diff',
        inverse_name='batch_id',
        readonly=True)
    bom_line_diff_ids = fields.One2many(
        comodel_name='engineering.bom.line.diff',
        inverse_name='batch_id',
        readonly=True)
    adjacency_count = fields.Integer(
        compute='_compute_adjacency_count',
        string='Adjacency Count',
        help='Number of adjacency records in this Batch')
    comp_count = fields.Integer(
        compute='_compute_component_count',
        string='Comp Count',
        help='Number of component records in this Batch')
    bom_count = fields.Integer(
        compute='_compute_bom_count',
        string='BOM Count',
        help='Number of BOM records in this Batch')
    part_diff_count = fields.Integer(
        compute='_compute_part_diff_count',
        string='Part Diff Count')
    bom_diff_count = fields.Integer(
        compute='_compute_bom_diff_count',
        string='BOM Diff Count')
    bom_line_diff_count = fields.Integer(
        compute='_compute_bom_line_diff_count',
        string='BOM Line Diff Count')

    @api.depends('adjacency_ids')
    def _compute_adjacency_count(self):
        for batch in self:
            batch.adjacency_count = len(self.adjacency_ids.ids)

    @api.depends('comp_ids')
    def _compute_component_count(self):
        for batch in self:
            batch.comp_count = len(self.comp_ids.ids)

    @api.depends('eng_bom_ids')
    def _compute_bom_count(self):
        for batch in self:
            batch.bom_count = len(self.eng_bom_ids.ids)

    @api.depends('part_diff_ids')
    def _compute_part_diff_count(self):
        for batch in self:
            batch.part_diff_count = len(self.part_diff_ids.ids)

    @api.depends('bom_diff_ids')
    def _compute_bom_diff_count(self):
        for batch in self:
            batch.bom_diff_count = len(self.bom_diff_ids.ids)

    @api.depends('bom_line_diff_ids')
    def _compute_bom_line_diff_count(self):
        for batch in self:
            batch.bom_line_diff_count = len(self.bom_line_diff_ids.ids)

    @api.multi
    def write(self, vals):
        # don't allow state to change if it's 'done'
        # if self.state == 'done' and vals.get('state', 'done') != 'done':
        #     raise UserError("Can't change state after it's done!")
        return super(EngBomBatch, self).write(vals)

    def action_match_component_products(self):
        self.ensure_one()
        for comp in self.comp_ids:
            comp.set_product()

    def action_convert_boms(self):
        self.ensure_one()

        self.eng_bom_ids.unlink()

        eng_bom_obj = self.env['engineering.bom']
        eng_bom_line_obj = self.env['engineering.bom.line']
        product_obj = self.env['product.product']
        bom_obj = self.env['mrp.bom']
        routing_obj = self.env['mrp.routing']
        attr_line_obj = self.env['product.template.attribute.line']

        # get unique parent products and create boms
        product_boms = {}
        duplicate_parents = []
        parents = self.comp_ids.filtered(
            lambda x: len(x.adjacency_parent_ids)
                      and not x.preserve_bom_on_import)
        for parent in parents:
            if not parent.product_id:
                continue
            if parent.product_id in product_boms.keys():
                duplicate_parents.append(parent.id)
                continue
            bom = bom_obj._bom_find(product=parent.product_id)
            route_template = routing_obj.search(
                [('name', '=', parent.route_template_name)],
                order="id ASC",
                limit=1,
            )
            bom_values = {
                'batch_id': self.id,
                'name': parent.product_id.id,
                'bom_id': bom.id,
                'quantity': 1.0,
                'route_template_id': route_template.id,
                'type': bom and bom.type or 'normal',
            }
            eng_bom = eng_bom_obj.create(bom_values)
            product_boms[parent.product_id] = eng_bom

        # get configurator options
        # TODO: check against all product versions
        # TODO: automatically get configurator templates based on imported products
        option_products = self.env['product.product']
        for tmpl in self.configurator_ids:
            top_bom = bom_obj.search(
                [('product_tmpl_id', '=', tmpl.id)],
                order='version desc, sequence asc',
                limit=1,
            )
            attr_val_prods = top_bom.bom_line_ids.mapped('product_id')
            for prod in attr_val_prods:
                if not prod.bom_ids:
                    continue
                opt_bom = prod.bom_ids[0]
                option_products |= opt_bom.bom_line_ids.mapped('product_id')
        self.option_component_ids = [(6, 0, option_products.ids)]

        # create bom lines
        product_bom_lines = {}
        adjacencies = self.adjacency_ids.filtered(
            lambda x: x.child_comp_id.eng_type_id.code != 'S'
                      and not x.parent_comp_id.preserve_bom_on_import)
        for adjacency in adjacencies:
            if not adjacency.parent_comp_id.product_id or not adjacency.child_comp_id.product_id:
                continue
            if adjacency.child_comp_id.product_id.id in self.option_component_ids.ids:
                # don't add option components as a child of any real BOM
                continue
            parent = adjacency.parent_comp_id.product_id
            child = adjacency.child_comp_id.product_id
            alt_qty = adjacency.child_comp_id.alt_qty
            quantity = alt_qty and adjacency.count * alt_qty or adjacency.count
            existing_line = product_bom_lines.get((parent, child))
            if existing_line:
                if adjacency.parent_comp_id.id not in duplicate_parents:
                    existing_line.quantity += quantity
                continue
            line_values = {
                'eng_bom_id': product_boms[parent].id,
                'name': child.id,
                'quantity': quantity,
            }
            line = eng_bom_line_obj.create(line_values)
            product_bom_lines[(parent, child)] = line

        # create raw material boms and lines
        raw_parents = self.comp_ids.filtered(lambda x: not len(x.adjacency_parent_ids) and x.rm_qty > 0.0)
        for parent in raw_parents:
            if (
                    not parent.product_id
                    or not parent.route_template_id
                    or not parent.rm_product_id
                    or parent.product_id in product_boms.keys()):
                continue
            rm_product = parent.rm_product_id
            route_template = parent.route_template_id
            if not rm_product or not route_template:
                continue
            bom = bom_obj._bom_find(product=parent.product_id)
            bom_values = {
                'batch_id': self.id,
                'name': parent.product_id.id,
                'bom_id': bom.id,
                'quantity': 1.0,
                'route_template_id': route_template.id,
                'type': bom and bom.type or 'normal',
                'rm_part': True,
            }
            eng_bom = eng_bom_obj.create(bom_values)
            product_boms[parent.product_id] = eng_bom
            line_values = {
                'eng_bom_id': eng_bom.id,
                'name': rm_product.id,
                'quantity': parent.rm_qty,
            }
            eng_bom_line_obj.create(line_values)

        self.state = 'converted'

    def action_get_diffs(self):
        self.ensure_one()
        self.make_part_diffs()
        self.make_bom_diffs()
        self.make_bom_line_diffs()
        self.state = 'comparing'

    def make_part_diffs(self):
        self.ensure_one()
        self.part_diff_ids.unlink()
        # precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        # create part diff records for this batch
        part_diff_obj = self.env['engineering.part.diff']
        to_delete = self.env['engineering.part.diff']
        unique_ids = set()
        for part in self.comp_ids.filtered(lambda x: x.product_id):
            if part.product_id.id in unique_ids:
                continue
            else:
                unique_ids.add(part.product_id.id)

            has_change = False
            is_important = False
            diff = part_diff_obj.create({
                'batch_id': self.id,
                'product_id': part.product_id.id,
            })

            if part.description != part.product_id.product_tmpl_id.name:
                has_change = True
                diff.description = part.product_id.product_tmpl_id.name
                diff.description_new = part.description
            if part.image and part.image != part.product_id.product_tmpl_id.image:
                has_change = True
                is_important = True
                diff.image = part.product_id.product_tmpl_id.image
                diff.image_new = part.image
            if part.eng_type_id != part.product_id.eng_type_id:
                has_change = True
                diff.eng_type_id = part.product_id.eng_type_id
                diff.eng_type_new_id = part.eng_type_id
            if part.product_id.make != part.make:
                has_change = True
                is_important = False
                diff.make = part.product_id.make
                diff.make_new = part.make
            if part.preparation_id != part.product_id.product_tmpl_id.preparation_id:
                has_change = True
                diff.preparation_id = part.product_id.product_tmpl_id.preparation_id
                diff.preparation_new_id = part.preparation_id
            if part.coating_id != part.product_id.product_tmpl_id.coating_id:
                has_change = True
                diff.coating_id = part.product_id.product_tmpl_id.coating_id
                diff.coating_new_id = part.coating_id
            if part.uom_id != part.product_id.product_tmpl_id.uom_id:
                has_change = True
                diff.uom_id = part.product_id.product_tmpl_id.uom_id
                diff.uom_new_id = part.uom_id
            if float_compare(
                    part.cutting_length_outer,
                    part.product_id.cutting_length_outer,
                    precision_digits=2) != 0:
                has_change = True
                is_important = True
                diff.cutting_length_outer = part.product_id.cutting_length_outer
                diff.cutting_length_outer_new = part.cutting_length_outer
            if float_compare(
                    part.cutting_length_inner,
                    part.product_id.cutting_length_inner,
                    precision_digits=2) != 0:
                has_change = True
                is_important = True
                diff.cutting_length_inner = part.product_id.cutting_length_inner
                diff.cutting_length_inner_new = part.cutting_length_inner
            if part.cut_out_count != part.product_id.cut_out_count:
                has_change = True
                is_important = True
                diff.cut_out_count = part.product_id.cut_out_count
                diff.cut_out_count_new = part.cut_out_count
            if part.bend_count != part.product_id.bend_count:
                has_change = True
                is_important = True
                diff.bend_count = part.product_id.bend_count
                diff.bend_count_new = part.bend_count

            if has_change:
                diff.important = is_important
                part.part_diff_id = diff
            else:
                to_delete |= diff
        to_delete.unlink()

        self.message_post(body="Generated part diffs")

    def make_bom_diffs(self):
        self.ensure_one()
        self.bom_diff_ids.unlink()

        bom_diff_obj = self.env['engineering.bom.diff']
        bom_obj = self.env['mrp.bom']

        # create add/change diffs for this batch
        to_delete = self.env['engineering.bom.diff']
        for eng_bom in self.eng_bom_ids:
            diff = bom_diff_obj.create({
                'batch_id': self.id,
                'eng_bom_id': eng_bom.id,
                'bom_id': eng_bom.bom_id.id,
                'product_id': eng_bom.name.id,
                'action_type': eng_bom.bom_id and 'change' or 'add',
                'rm_part': eng_bom.rm_part,
            })

            if not eng_bom.bom_id:
                continue
            diff.qty = eng_bom.bom_id.product_qty

            has_change = False
            if eng_bom.quantity != eng_bom.bom_id.product_qty:
                has_change = True
                diff.qty = eng_bom.bom_id.product_qty
                diff.qty_new = eng_bom.quantity
            if eng_bom.route_template_id.operation_ids.mapped('workcenter_id') != \
                    eng_bom.bom_id.routing_id.operation_ids.mapped('workcenter_id'):
                has_change = True
                diff.route_template_id = eng_bom.bom_id.routing_id
                diff.route_template_new_id = eng_bom.route_template_id
            if eng_bom.type != eng_bom.bom_id.type:
                has_change = True
                diff.type = eng_bom.bom_id.type
                diff.type_new = eng_bom.type

            if not has_change:
                to_delete |= diff
        to_delete.unlink()

        # create remove diffs for this batch
        for part in self.comp_ids.filtered(
                lambda x: x.product_id
                          and not len(x.adjacency_parent_ids)
                          and not x.rm_product_id
                          and not x.preserve_bom_on_import):
            bom = bom_obj.search([('product_id', '=', part.product_id.id)], limit=1)
            if bom:
                diff = bom_diff_obj.create({
                    'batch_id': self.id,
                    'bom_id': bom.id,
                    'product_id': bom.product_id.id,
                    'route_template_id': bom.routing_id.id,
                    'type': bom.type,
                    'action_type': 'remove',
                    'rm_part': bom.one_comp_product_id and bom.one_comp_product_id.product_tmpl_id.is_continuous,
                })

        self.message_post(body="Generated BOM diffs")

    def make_bom_line_diffs(self):
        self.ensure_one()
        self.bom_line_diff_ids.unlink()

        line_diff_obj = self.env['engineering.bom.line.diff']
        bom_obj = self.env['mrp.bom']
        qty_precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        # create bom line diff records for this batch
        for eng_bom in self.eng_bom_ids:

            # new bom - all lines are added
            if not eng_bom.bom_id:
                for eng_line in eng_bom.bom_line_ids:
                    line_diff_obj.create({
                        'batch_id': self.id,
                        'eng_bom_id': eng_bom.id,
                        'eng_bom_line_id': eng_line.id,
                        'parent_id': eng_bom.name.id,
                        'name': eng_line.name.id,
                        'qty_new': eng_line.quantity,
                        'rm_part': eng_bom.rm_part,
                        'action_type': 'add',
                    })
                continue

            # if eng_bom.bom_id.one_comp_product_id and \
            #         eng_bom.bom_id.one_comp_product_id.product_tmpl_id.is_continuous:
            #     # for raw material part boms, we won't delete existing boms or
            #     # the single product line.
            #     # odoo data takes precedence over the imported data.
            #     # we will show a diff, but we won't apply these changes
            #     continue

            mrp_lines = eng_bom.bom_id.bom_line_ids
            eng_lines = eng_bom.bom_line_ids
            is_rm_part = eng_bom.rm_part

            # deleted components
            del_products = set(mrp_lines.mapped('product_id').ids) - set(eng_lines.mapped('name').ids)
            del_lines = mrp_lines.search([('id', 'in', mrp_lines.ids), ('product_id', 'in', list(del_products))])
            for mrp_line in del_lines:
                if mrp_line.product_id in self.option_component_ids:
                    action_type = 'option'
                else:
                    action_type = 'remove'
                line_diff_obj.create({
                    'batch_id': self.id,
                    'eng_bom_id': eng_bom.id,
                    'mrp_bom_line_id': mrp_line.id,
                    'parent_id': eng_bom.name.id,
                    'name': mrp_line.product_id.id,
                    'qty': mrp_line.product_qty,
                    'qty_new': 0.0,
                    'rm_part': is_rm_part,
                    'action_type': action_type,
                })

            # added components
            add_products = set(eng_lines.mapped('name').ids) - set(mrp_lines.mapped('product_id').ids)
            add_lines = eng_lines.search([('id', 'in', eng_lines.ids), ('name', 'in', list(add_products))])
            for eng_line in add_lines:
                line_diff_obj.create({
                    'batch_id': self.id,
                    'eng_bom_id': eng_bom.id,
                    'parent_id': eng_bom.name.id,
                    'name': eng_line.name.id,
                    'qty_new': eng_line.quantity,
                    'rm_part': is_rm_part,
                    'action_type': 'add',
                })

            # changed components
            common_products = set(eng_lines.mapped('name').ids).intersection(set(mrp_lines.mapped('product_id').ids))
            if not len(common_products):
                continue
            eng_common_lines = eng_lines.search([('id', 'in', eng_lines.ids), ('name', 'in', list(common_products))])
            mrp_line_group = mrp_lines.read_group(
                domain=[('id', 'in', mrp_lines.ids)],
                fields=['product_id', 'product_qty'],
                groupby=['product_id'])
            mrp_product_qty = {x['product_id'][0]: x['product_qty'] for x in mrp_line_group}
            for eng_line in eng_common_lines:
                mrp_line = mrp_lines.search([('id', 'in', mrp_lines.ids), ('product_id', '=', eng_line.name.id)],
                                            limit=1)
                eng_qty = eng_line.quantity
                mrp_qty = mrp_product_qty.get(eng_line.name.id, 0.0)
                qty_change = float_compare(eng_qty, mrp_qty, precision_digits=qty_precision) != 0
                uom_change = eng_line.uom_id != mrp_line.product_uom_id
                if qty_change or uom_change:
                    line_diff_obj.create({
                        'batch_id': self.id,
                        'eng_bom_id': eng_bom.id,
                        'mrp_bom_line_id': mrp_line.id,
                        'parent_id': eng_bom.name.id,
                        'name': eng_line.name.id,
                        'qty': qty_change and mrp_qty or False,
                        'qty_new': qty_change and eng_qty or False,
                        'uom_id': uom_change and mrp_line.product_uom_id.id or False,
                        'uom_new_id': uom_change and eng_line.uom_id.id or False,
                        'rm_part': is_rm_part,
                        'action_type': 'change',
                    })

        # create line diffs for removed boms
        for part in self.comp_ids.filtered(
                lambda x: x.product_id
                          and not len(x.adjacency_parent_ids)
                          and not x.rm_product_id
                          and not x.preserve_bom_on_import):
            bom = bom_obj.search([('product_id', '=', part.product_id.id)], limit=1)
            is_mrp_rm_part = bom.one_comp_product_id and \
                             bom.one_comp_product_id.product_tmpl_id.is_continuous
            # if is_mrp_rm_part:
            #     # for raw material part boms, we won't delete existing boms or
            #     # the single product line.
            #     # odoo data takes precedence over the imported data.
            #     # we will show a diff, but we won't apply these changes
            #     continue
            if bom:
                for mrp_line in bom.bom_line_ids:
                    line_diff_obj.create({
                        'batch_id': self.id,
                        'mrp_bom_line_id': mrp_line.id,
                        'parent_id': bom.product_id.id,
                        'name': mrp_line.product_id.id,
                        'qty': mrp_line.product_qty,
                        'qty_new': 0.0,
                        'rm_part': is_mrp_rm_part,
                        'action_type': 'remove',
                    })

        self.message_post(body="Generated BOM line diffs")

    def action_apply_part_diffs(self):

        # self.make_part_diffs()
        make_route = self.env.ref('mrp.route_warehouse0_manufacture')

        # update important product differences
        for part in self.comp_ids.filtered(lambda x: x.product_id and x.part_diff_id.important):
            if part.image and part.image != part.product_id.product_tmpl_id.image:
                part.product_id.product_tmpl_id.image = part.image
            if part.eng_type_id != part.product_id.eng_type_id:
                part.product_id.eng_type_id = part.eng_type_id
            if part.product_id.make != part.make:
                route_ids = set(part.product_id.route_ids.ids)
                route_ids.add(make_route.id)
                part.product_id.route_ids = list(route_ids)
            if part.preparation_id != part.product_id.product_tmpl_id.preparation_id:
                part.product_id.product_tmpl_id.preparation_id = part.preparation_id
            if part.coating_id != part.product_id.product_tmpl_id.coating_id:
                part.product_id.product_tmpl_id.coating_id = part.coating_id
            if float_compare(
                    part.cutting_length_outer,
                    part.product_id.cutting_length_outer,
                    precision_digits=2) != 0:
                part.product_id.cutting_length_outer = part.cutting_length_outer
            if float_compare(
                    part.cutting_length_inner,
                    part.product_id.cutting_length_inner,
                    precision_digits=2) != 0:
                part.product_id.cutting_length_inner = part.cutting_length_inner
            if part.cut_out_count != part.product_id.cut_out_count:
                part.product_id.cut_out_count = part.cut_out_count
            if part.bend_count != part.product_id.bend_count:
                part.product_id.bend_count = part.bend_count

        self.message_post(body="Applied important part diffs")

    def action_apply_bom_diffs(self):

        self.make_bom_diffs()
        self.make_bom_line_diffs()

        bom_obj = self.env['mrp.bom']
        bom_line_obj = self.env['mrp.bom.line']
        qty_precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        # change boms
        for eng_bom in self.eng_bom_ids.filtered(lambda x: x.bom_id):

            # for raw material part boms, we won't change quantity
            # odoo data takes precedence over the imported data
            # we do show a diff, but we won't apply these changes
            mrp_is_one_comp = eng_bom.bom_id.one_comp_product_id and \
                              eng_bom.bom_id.one_comp_product_id.product_tmpl_id.is_continuous

            mrp_lines = eng_bom.bom_id.bom_line_ids
            eng_lines = eng_bom.bom_line_ids

            # change the produced quantity
            if eng_bom.quantity != eng_bom.bom_id.product_qty:
                eng_bom.bom_id.product_qty = eng_bom.quantity

            # change routing
            route_changed = eng_bom.route_template_id and eng_bom.bom_id.routing_id and \
                            eng_bom.route_template_id.operation_ids.mapped('workcenter_id') != \
                            eng_bom.bom_id.routing_id.operation_ids.mapped('workcenter_id') or \
                            False
            # remove routing
            if route_changed or (eng_bom.bom_id.routing_id and not eng_bom.route_template_id):
                eng_bom.bom_id.routing_id.unlink()
            # add new routing
            if route_changed or (eng_bom.route_template_id and not eng_bom.bom_id.routing_id):
                route = eng_bom.route_template_id.copy()
                route.name = eng_bom.name.eng_code
                eng_bom.bom_id.routing_id = route

            # change bom type
            if eng_bom.type != eng_bom.bom_id.type:
                eng_bom.bom_id.type = eng_bom.type

            # add bom lines
            add_products = set(eng_lines.mapped('name').ids) - set(mrp_lines.mapped('product_id').ids)
            add_lines = eng_lines.search([('id', 'in', eng_lines.ids), ('name', 'in', list(add_products))])
            for eng_line in add_lines:
                line_vals = {
                    'bom_id': eng_bom.bom_id.id,
                    'product_id': eng_line.name.id,
                    'product_qty': eng_line.quantity,
                    'product_uom_id': eng_line.uom_id.id,
                }
                bom_line_obj.create(line_vals)

            # change bom lines
            common_products = set(eng_lines.mapped('name').ids).intersection(set(mrp_lines.mapped('product_id').ids))
            if len(common_products):
                eng_common_lines = eng_lines.search(
                    [('id', 'in', eng_lines.ids), ('name', 'in', list(common_products))])
                for eng_line in eng_common_lines:
                    mrp_product_lines = mrp_lines.search(
                        [('id', 'in', mrp_lines.ids), ('product_id', '=', eng_line.name.id)])
                    mrp_qty = sum(mrp_product_lines.mapped('product_qty'))
                    if len(mrp_product_lines) > 1:
                        # TODO: handle product lines that have been intentionally
                        #  duplicated for usage in different workcenters
                        # merge duplicate product lines
                        mrp_product_lines[1:].unlink()
                        mrp_product_lines[0].product_qty = mrp_qty
                    mrp_line = mrp_product_lines[0]
                    eng_qty = eng_line.quantity
                    qty_change = float_compare(eng_qty, mrp_qty, precision_digits=qty_precision) != 0
                    uom_change = eng_line.uom_id != mrp_line.product_uom_id
                    if qty_change or uom_change:
                        if not mrp_is_one_comp:
                            # TODO: check for uom mismatch and convert qty if necessary
                            mrp_line.product_qty = eng_qty
                            mrp_line.product_uom_id = eng_line.uom_id

            # delete bom lines
            del_products = set(eng_bom.bom_id.bom_line_ids.mapped('product_id').ids) - set(eng_lines.mapped('name').ids)
            del_lines = mrp_lines.search([('id', 'in', mrp_lines.ids), ('product_id', 'in', list(del_products))])
            del_lines.unlink()

        # add boms
        for eng_bom in self.eng_bom_ids.filtered(lambda x: not x.bom_id):
            # create bom and component line
            bom_vals = {
                'product_id': eng_bom.name.id,
                'type': eng_bom.type,
                'product_tmpl_id': eng_bom.name.product_tmpl_id.id,
                'code': eng_bom.name.default_code,
                'product_qty': eng_bom.quantity,
                'product_uom_id': eng_bom.name.product_tmpl_id.uom_id.id,
                'sequence': 1,
            }
            new_bom = bom_obj.create(bom_vals)
            eng_bom.bom_id = new_bom

            # add routing
            if eng_bom.route_template_id:
                route = eng_bom.route_template_id.copy()
                route.name = eng_bom.name.default_code
                new_bom.routing_id = route

            # add bom lines
            for eng_line in eng_bom.bom_line_ids:
                line_vals = {
                    'bom_id': new_bom.id,
                    'product_id': eng_line.name.id,
                    'product_qty': eng_line.quantity,
                    'product_uom_id': eng_line.uom_id.id,
                }
                bom_line_obj.create(line_vals)

        # delete boms
        for part in self.comp_ids.filtered(
                lambda x: x.product_id
                          and not len(x.adjacency_parent_ids)
                          and not x.rm_product_id
                          and not x.preserve_bom_on_import):
            # for raw material part boms, we won't delete existing boms
            # odoo data takes precedence over the imported data
            # we do show a diff, but we won't apply these changes
            domain = [('product_id', '=', part.product_id.id)]
            boms = bom_obj.search(domain).filtered(
                lambda x: not x.one_comp_product_id
                          or not x.one_comp_product_id.is_continuous)
            boms.unlink()

        self.state = 'done'
