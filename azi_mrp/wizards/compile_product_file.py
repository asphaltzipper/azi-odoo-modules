# -*- coding: utf-8 -*-
import base64
from io import BytesIO
from PyPDF2 import PdfFileReader, PdfFileWriter


from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class CompileProductFile(models.TransientModel):
    _name = 'compile.product.file'

    bom_depth = fields.Integer('BOM Depth', default=1)
    included_files = fields.Selection([('high', 'Highest Priority PDFs Only'), ('pdf', 'All PDFs')])
    compiled_file = fields.Binary('Compiled File')
    compiled_filename = fields.Char('File Name')

    @api.constrains('bom_depth')
    def _check_bom_depth(self):
        if self.bom_depth <= 0:
            raise ValidationError(_('BOM Depth should be greater than zero'))

    def _get_returned_attachment(self, attachments_with_order):
        returned_attachments = []
        if self.included_files == 'high':
            for attachment in attachments_with_order:
                to_attach = attachment[3].filtered(lambda a: a.priority == '3' and a.mimetype.split('/')[1] == 'pdf')
                to_attach and returned_attachments.extend(to_attach)
        else:
            for attachment in attachments_with_order:
                to_attach = attachment[3].filtered(lambda a: a.mimetype.split('/')[1] == 'pdf')
                to_attach and returned_attachments.extend(to_attach)
        return returned_attachments

    def action_show_files(self):
        context = self._context.copy()
        returned_attachments = []
        output = PdfFileWriter()
        for active_id in context['active_ids']:
            # structure (level, parent_product_id, product_id, attachment)
            attachments_with_level = []
            level = 1
            if context['active_model'] == 'product.template':
                bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', active_id)], limit=1)
            else:
                bom = self.env['mrp.bom'].search([('product_id', '=', active_id)], limit=1)
            attach = self.env['ir.attachment'].search([
                '|',
                '&', ('res_model', '=', 'product.product'), ('res_id', '=', bom.product_id.id),
                '&', ('res_model', '=', 'product.template'), ('res_id', '=', bom.product_tmpl_id.id)])
            attachments_with_level.append((level, bom.product_id.id, bom.product_id.id, attach))
            for line in bom.bom_line_ids:
                level = 1
                product = line.product_id
                i = 1
                attach = self.env['ir.attachment'].search([
                    '|',
                    '&', ('res_model', '=', 'product.product'), ('res_id', '=', product.id),
                    '&', ('res_model', '=', 'product.template'), ('res_id', '=', product.product_tmpl_id.id)])
                attachments_with_level.append((level, line.bom_id.product_id.id, line.product_id.id, attach))
                childs = line.child_line_ids
                while childs and i < self.bom_depth:
                    level += 1
                    for child in childs:
                        attach = self.env['ir.attachment'].search([
                            '|',
                            '&', ('res_model', '=', 'product.product'), ('res_id', '=', child.product_id.id),
                            '&', ('res_model', '=', 'product.template'),
                            ('res_id', '=', child.product_id.product_tmpl_id.id)])
                        attachments_with_level.append((level, child.bom_id.product_id.id,
                                                                  child.product_id.id, attach))
                    i += 1
                    childs = childs.mapped('child_line_ids')
            attachments_with_order = []
            for i in range(1, self.bom_depth + 1):
                temp = [attach for attach in attachments_with_level if attach[0] == i]
                if not attachments_with_order:
                    attachments_with_order = temp
                else:
                    if temp:
                        index = [attach[2] for attach in attachments_with_order].index(temp[0][1])
                        for item in temp:
                            index = index + 1
                            attachments_with_order.insert(index, item)
                    else:
                        break
            returned_attachments.extend(self._get_returned_attachment(attachments_with_order))
        for attachment in returned_attachments:
            attachment_report = PdfFileReader(attachment._full_path(attachment.store_fname), 'rb')
            for page in range(attachment_report.getNumPages()):
                output.addPage(attachment_report.getPage(page))
        output_stream = BytesIO()
        output.write(output_stream)
        self.compiled_file = base64.b64encode(output_stream.getvalue())
        self.compiled_filename = "Compiled PDFs.pdf"
        output_stream.close()
        return {
            'type': 'ir.actions.act_url',
            'name': 'Compiled PDFs',
            'url': '/web/content/compile.product.file/%s/compiled_file/Compiled PDFs.pdf?download=true' % (
                self.id),
        }
