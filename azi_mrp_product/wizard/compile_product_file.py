# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class CompileProductFile(models.TransientModel):
    _name = 'compile.product.file'

    bom_depth = fields.Integer('BOM Depth', default=1)
    included_files = fields.Selection([('high', 'Highest Priority PDFs Only'), ('pdf', 'All PDFs'),
                                       ('files', 'All Files')])

    @api.constrains('bom_depth')
    def _check_bom_depth(self):
        if self.bom_depth <= 0:
            raise ValidationError(_('BOM Depth should be greater than zero'))

    def action_show_files(self):
        context = self._context.copy()
        context.update(active_id=[context['active_id']])
        attachments = []
        returned_attachments = []
        for i in range(self.bom_depth):
            product_child = []
            if context['active_model'] == 'product.template':
                boms = self.env['mrp.bom'].search([('product_tmpl_id', 'in', context['active_id'])])
            else:
                boms = self.env['mrp.bom'].search([('product_id', 'in', context['active_id'])])
            products = boms.mapped('bom_line_ids').mapped('product_id')
            if products:
                product_child = products.ids
                attach = self.env['ir.attachment'].search([('res_model', '=', 'product.product'),
                                                           ('res_id', 'in', products.ids)])
                attach and attachments.append(attach)
            context['active_model'] = 'product.product'
            context['active_id'] = product_child

        if self.included_files == 'high':
            for attachment in attachments:
                to_attach = attachment.filtered(lambda a: a.priority == '3').ids
                to_attach and returned_attachments.extend(to_attach)
        elif self.included_files == 'pdf':
            for attachment in attachments:
                to_attach = attachment.filtered(lambda a: a.mimetype.split('/')[1] == 'pdf').ids
                to_attach and returned_attachments.extend(to_attach)
        else:
            for attachment in attachments:
                to_attach = attachment.ids
                to_attach and returned_attachments.extend(to_attach)
        attachment_view = self.env.ref('attachment_priority.view_ir_attachment_kanban')
        return {
            'name': _('Compiled Attachments'),
            'domain': [('id', 'in', tuple(returned_attachments))],
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_id': attachment_view.id,
            'views': [(attachment_view.id, 'kanban'), (False, 'form')],
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'limit': 80,
        }

