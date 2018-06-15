# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError


class MfgCreateBom(models.TransientModel):
    _name = 'mfg.create.bom'
    _description = 'Create BOM for MFG Integration'

    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string="Mfg Product",
        readonly=True)
    rm_product_id = fields.Many2one(
        comodel_name='product.product',
        string="Raw Material",
        required=True,
        domain=[('is_continuous', '=', True)],
        help="Only products with continuous UOM will show here.")
    rm_uom_id = fields.Many2one(
        comodel_name='product.uom',
        related='rm_product_id.uom_id',
        string="RM Units",
        readonly=True)
    rm_qty = fields.Float(
        string="RM Qty",
        required=True)
    routing_id = fields.Many2one(
        comodel_name='mrp.routing',
        string="Routing Template",
        required=True,
        domain=[('name', 'like', 'template')],
        help="Only routings with 'template' in the name will show here.")

    @api.model
    def default_get(self, fields):
        result = super(MfgCreateBom, self).default_get(fields)
        product_tmpl_id = self.env.context.get('active_id')
        if product_tmpl_id:
            result['product_tmpl_id'] = product_tmpl_id
        return result

    @api.multi
    def button_create_bom(self):
        """
        Modify an old BOM if only the raw material quantity is changing.  That is to say:
            - We are not changing the raw material product
            - We are not changing the routing workcenters or sequence
        Otherwise, create a new BOM
        """
        self.ensure_one()
        if not self.product_tmpl_id:
            raise UserError('Wizard called with no product template')
        if not self.product_tmpl_id.product_variant_ids:
            raise UserError('No active products associated with this product template')

        # get existing BOMs
        boms = self.env['mrp.bom'].search([('product_tmpl_id', '=', self.product_tmpl_id.id)])
        old_bom = boms and boms[0] or False

        if old_bom:
            if not old_bom.one_comp_product_id:
                raise UserError(
                    "You are attempting to replace a BOM that does not have "
                    "exactly one component.  Either, delete the existing BOM, or "
                    "create the new BOM manually.")

            if old_bom.one_comp_product_id.id == self.rm_product_id.id:
                if old_bom.routing_id and old_bom.routing_id.mapped('operation_ids.workcenter_id') == \
                        self.routing_id.mapped('operation_ids.workcenter_id'):
                    # don't worry about uom because the old bom probably used the stocking uom
                    old_bom.bom_line_ids[0].product_qty = self.rm_qty
                    return {'type': 'ir.actions.act_window_close'}

        if boms:
            # we are going to make a new BOM
            # advance sequence on existing BOMs
            i = 2
            for bom in boms:
                bom.sequence = i
                i += 1
                # bom.active = False

        # create bom and component line
        bom_vals = {
            'product_id': self.product_tmpl_id.product_variant_ids[0].id,
            'type': 'normal',
            'product_tmpl_id': self.product_tmpl_id.id,
            'code': self.product_tmpl_id.default_code,
            'product_qty': '1',
            'product_uom_id': self.product_tmpl_id.uom_id.id,
            'sequence': 1,
        }
        new_bom = self.env['mrp.bom'].create(bom_vals)
        line_vals = {
            'bom_id': new_bom.id,
            'product_id': self.rm_product_id.id,
            'product_qty': self.rm_qty,
            'product_uom_id': self.rm_uom_id.id,
        }
        self.env['mrp.bom.line'].create(line_vals)

        if old_bom and old_bom.routing_id and old_bom.routing_id.mapped('operation_ids.workcenter_id') == \
                self.routing_id.mapped('operation_ids.workcenter_id'):
            # use the old routing
            new_bom.routing_id = old_bom.routing_id.id
        else:
            # create a new routing
            new_route = self.routing_id.copy()
            new_route.name = self.product_tmpl_id.eng_code
            new_bom.routing_id = new_route.id

        return {'type': 'ir.actions.act_window_close'}
