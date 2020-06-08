# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    # require product variant on every bom
    # isn't there a way to do this without overriding the entire definition?
    # product_id = fields.Many2one(required=True)
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product Variant',
        required=True,
        domain="['&', ('product_tmpl_id', '=', product_tmpl_id), ('type', 'in', ['product', 'consu'])]",
        help="If a product variant is defined the BOM is available only for this product.")

    re_config = fields.Boolean('Re-config')

    # null sorts last??!!
    # the default is null??!!!
    # I thought integer fields could not be null?
    # okay, make the default one
    sequence = fields.Integer(default=1)

    @api.constrains('product_id', 'product_tmpl_id', 'bom_line_ids', 're_config')
    def _check_product_recursion(self):
        for bom in self:
            if not bom.re_config:
                if bom.product_id:
                    if bom.bom_line_ids.filtered(lambda x: x.product_id == bom.product_id):
                        raise ValidationError(
                            _('BoM line product %s should not be same as BoM product.') % bom.display_name)
                else:
                    if bom.bom_line_ids.filtered(lambda x: x.product_id.product_tmpl_id == bom.product_tmpl_id):
                        raise ValidationError(
                            _('BoM line product %s should not be same as BoM product.') % bom.display_name)


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    @api.one
    @api.depends('product_id')
    def _compute_has_attachments(self):
        nbr_attach = self.env['ir.attachment'].search_count([
            '|',
            '&', ('res_model', '=', 'product.product'), ('res_id', '=', self.product_id.id),
            '&', ('res_model', '=', 'product.template'), ('res_id', '=', self.product_id.product_tmpl_id.id)])
        self.has_attachments = bool(nbr_attach)

    @api.multi
    def action_see_attachments(self):
        domain = [
            '|',
            '&', ('res_model', '=', 'product.product'), ('res_id', '=', self.product_id.id),
            '&', ('res_model', '=', 'product.template'), ('res_id', '=', self.product_id.product_tmpl_id.id)]
        attachment_view = self.env.ref('attachment_priority.view_ir_attachment_kanban')
        return {
            'name': _('Attachments'),
            'domain': domain,
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_id': attachment_view.id,
            'views': [(attachment_view.id, 'kanban'), (False, 'form')],
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'help': _('''<p class="o_view_nocontent_smiling_face">
                            Upload files to your product
                        </p><p>
                            Use this feature to store any files, like drawings or specifications.
                        </p>'''),
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d}" % ('product.product', self.product_id.id)
        }
