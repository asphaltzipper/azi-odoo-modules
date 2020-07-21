# -*- coding: utf-8 -*-
import datetime
import base64
from io import BytesIO
from PyPDF2 import PdfFileReader, PdfFileWriter


from odoo import fields, models, api


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    date_planned_start = fields.Datetime(
        string='Deadline Start',
        copy=False,
        default=fields.Datetime.now,
        index=True,
        required=True,
        oldname="date_planned",
        compute='_compute_date_planned_start',
        store=True)

    moves_plus = fields.One2many(
        comodel_name='production.move.analysis',
        inverse_name='raw_material_production_id',
        readonly=True
    )
    report_attach = fields.Binary()
    report_name = fields.Char()

    @api.depends('date_planned_finished', 'product_id.produce_delay')
    def _compute_date_planned_start(self):
        for production in self:
            production.date_planned_start = production.date_planned_finished - datetime.timedelta(
                days=int(production.product_id.produce_delay))

    # select *
    # from mrp_bom as b
    # left join product_template as t on t.id=b.product_tmpl_id
    # where b.routing_id is null
    # and t.deprecated=false
    # and b.type='normal'
    # and b.product_id in (

    @api.multi
    def write(self, vals):
        """Override wirte method to update stock move expected date that is related to mrp production"""
        res = super(MrpProduction, self).write(vals)
        if 'date_planned_finished' in vals or 'date_planned_start' in vals:
            for record in self:
                date_planned_start = 'date_planned_start' in vals and vals[
                    'date_planned_start'] or record.date_planned_start
                moves = self.env['stock.move'].search(['|', ('raw_material_production_id', '=', record.id),
                                                       ('production_id', '=', record.id),
                                                       ('state', 'not in', ('cancel', 'done'))])
                moves.sudo().write({'date_expected': date_planned_start,
                                    'date': date_planned_start})
                move_lines = moves.mapped('move_line_ids')
                move_lines and move_lines.sudo().write({'date': date_planned_start})
        return res

    @api.multi
    def print_production_and_attachment(self):
        self.ensure_one()
        report = self.env['ir.actions.report']._get_report_from_name('azi_mrp.report_mrporder_azi')
        attachment = self.env['ir.attachment'].search(
            [('mimetype', '=', 'application/pdf'),
             ('res_model', '=', 'product.product'),
             ('res_id', '=', self.product_id.id)],
            order='priority desc, name', limit=1)
        if not attachment:
            attachment = self.env['ir.attachment'].search(
                [('mimetype', '=', 'application/pdf'),
                 ('res_model', '=', 'product.template'),
                 ('res_id', '=', self.product_id.product_tmpl_id.id)],
                order='priority desc, name', limit=1)
        report_bytes, _ = report.render_qweb_pdf(res_ids=self.id)
        buffer = BytesIO(report_bytes)
        production_pdf = PdfFileReader(buffer)
        output = PdfFileWriter()
        for page in range(production_pdf.getNumPages()):
            output.addPage(production_pdf.getPage(page))
        if attachment:
            attachment_report = PdfFileReader(attachment._full_path(attachment.store_fname), 'rb')
            for page in range(attachment_report.getNumPages()):
                output.addPage(attachment_report.getPage(page))
        output_stream = BytesIO()
        output.write(output_stream)
        self.report_attach = base64.b64encode(output_stream.getvalue())
        self.report_name = "Azi Production Order with Attachment.pdf"
        output_stream.close()
        return {
            'type': 'ir.actions.act_url',
            'name': 'Azi Production',
            'target': 'self',
            'url': '/web/content/mrp.production/%s/report_attach/Azi Production Order with Attachment.pdf?download=true'
                   % self.id,
        }
