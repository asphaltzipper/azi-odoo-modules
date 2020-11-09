import base64
from io import BytesIO
from PyPDF2 import PdfFileReader, PdfFileWriter


from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError


class CompileProductFile(models.TransientModel):
    _name = 'compile.product.file'
    _description = "Compile Product Files"

    bom_depth = fields.Integer('BOM Depth', default=1)
    included_files = fields.Selection([('high', 'Highest Priority PDFs Only'), ('pdf', 'All PDFs')])
    compiled_file = fields.Binary('Compiled File')
    compiled_filename = fields.Char('File Name')

    @api.constrains('bom_depth')
    def _check_bom_depth(self):
        if self.bom_depth <= 0:
            raise ValidationError(_('BOM Depth should be greater than zero'))

    def _get_structure_recursion(self, product, limit, path='', level=0):
        current_path = path + '|' + product.display_name
        stack = {current_path: product}
        if level >= limit or not product.bom_ids:
            return stack
        for line in product.bom_ids[0].bom_line_ids:
            stack.update(self._get_structure_recursion(
                line.product_id, limit, current_path, level+1))
        return stack

    def _get_attachments(self, product, get_all):
        attachments = self.env['ir.attachment'].search([
            ('res_field', '=', False),
            ('mimetype', '=', 'application/pdf'),
            '|',
            '&', ('res_model', '=', 'product.product'), ('res_id', '=', product.id),
            '&', ('res_model', '=', 'product.template'), ('res_id', '=', product.product_tmpl_id.id),
        ], order='priority desc')
        if attachments and not get_all:
            # return only the highest priority attachment
            return attachments[0]
        else:
            return attachments

    def action_show_files(self):
        context = self._context.copy()
        bom_structure = {}
        output = PdfFileWriter()

        # get bom structure
        for active_id in context['active_ids']:
            if context['active_model'] == 'product.template':
                top_template = self.env['product.template'].browse(active_id)
                if len(top_template.product_variant_ids) > 1:
                    raise UserError(_(
                        "Can't compile PDFs for template with multiple variants:\n%s" % top_template))
                top_product = top_template.product_variant_ids
            else:
                top_product = self.env['product.product'].browse(active_id)
            bom_structure.update(self._get_structure_recursion(top_product, self.bom_depth))

        # get and compile pdf attachments
        for key in sorted(bom_structure):
            attachments = self._get_attachments(
                bom_structure[key],
                self.included_files == 'all')
            for attachment in attachments:
                try:
                    attachment_report = PdfFileReader(attachment._full_path(attachment.store_fname), strict=False)
                except Exception as e:
                    value = '. '.join(e.args)
                    raise UserError(_("Failed to include %s:\n%s" % (attachment.name, value)))
                for page in range(attachment_report.getNumPages()):
                    output.addPage(attachment_report.getPage(page))

        # encode and return compiled document
        output_stream = BytesIO()
        output.write(output_stream)
        self.compiled_file = base64.b64encode(output_stream.getvalue())
        self.compiled_filename = "Compiled PDFs.pdf"
        output_stream.close()
        return {
            'type': 'ir.actions.act_url',
            'name': 'Compiled PDFs',
            'url': '/web/content/compile.product.file/%s/compiled_file/Compiled PDFs.pdf?download=true' % self.id,
        }
