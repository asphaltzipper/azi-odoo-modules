# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    # null sorts last??!!
    # the default is null??!!!
    # I thought integer fields could not be null?
    # okay, make the default one
    sequence = fields.Integer(default=1)

    def rpc_explode(self, product_id, quantity, picking_type_id=False):
        product = self.env['product.product'].browse(product_id)
        if picking_type_id:
            picking_type = self.env['picking.type'].browse(picking_type_id)
        else:
            picking_type = False
        boms, lines = self.explode(product, quantity, picking_type)
        boms_done = []
        for bom in boms:
            bom_row = (bom[0].id, {
                'product_id': bom[1]['product'].id,
                'parent_line_id': bom[1]['parent_line'] and bom[1]['parent_line'].id or False,
                'qty': bom[1]['qty'],
                'original_qty': bom[1]['original_qty'],
            })
            boms_done.append(bom_row)
        lines_done = []
        for line in lines:
            line_row = (line[0].id, {
                'product_id': line[1]['product'].id,
                'parent_line_id': line[1]['parent_line'] and line[1]['parent_line'].id or False,
                'qty': line[1]['qty'],
                'original_qty': line[1]['original_qty'],
            })
            lines_done.append(line_row)
        return boms_done, lines_done


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
