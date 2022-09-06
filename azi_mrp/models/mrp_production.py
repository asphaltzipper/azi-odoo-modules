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
    def get_production_and_attachment(self):
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
        with BytesIO() as output_stream:
            output.write(output_stream)
            self.report_attach = base64.b64encode(output_stream.getvalue())
            self.report_name = "Azi Production Order with Attachment.pdf"

    @api.multi
    def print_production_and_attachment(self):
        self.get_production_and_attachment()
        printer_obj = self.env['printing.printer']
        user = self.env.user
        printer = user.printing_printer_id or printer_obj.get_default()
        if not printer:
            message = "No printer configured to print %s" % self.name
            self.env.user.notify_warning(message=message, title="Print MO", sticky=False)
            return {
                'type': 'ir.actions.act_url',
                'name': 'Azi Production',
                'target': 'self',
                'url': '/web/content/mrp.production/%s/report_attach/'
                       'Azi Production Order with Attachment.pdf?download=true'
                       % self.id,
            }
        tray = str(user.printer_tray_id.system_name) if user.printer_tray_id else False
        printer.print_document(
            self,
            base64.b64decode(self.report_attach),
            doc_format='qweb-pdf',
            action='print',
            tray=tray,
        )
        message = "MO sent to printer %s" % printer.name
        self.env.user.notify_success(message=message, title="Print MO", sticky=False)
        return {}

    @api.multi
    def direct_print_azi_report(self):
        self.ensure_one()
        report = self.env['ir.actions.report']._get_report_from_name('azi_mrp.report_mrporder_azi')
        report_bytes, _ = report.render_qweb_pdf(res_ids=self.id)
        printer_obj = self.env['printing.printer']
        user = self.env.user
        printer = user.printing_printer_id or printer_obj.get_default()
        if not printer:
            message = "No printer configured to print %s" % self.name
            self.env.user.notify_warning(message=message, title="Print MO", sticky=False)
            return False
        tray = str(user.printer_tray_id.system_name) if user.printer_tray_id else False
        printer.print_document(
            report,
            report_bytes,
            doc_format='qweb-pdf',
            action='print',
            tray=tray,
        )
        message = "MO sent to printer %s" % printer.name
        self.env.user.notify_success(message=message, title="Print MO", sticky=False)
        return True

    @api.multi
    def direct_print_product_attachment(self):
        self.ensure_one()
        printer_obj = self.env['printing.printer']
        user = self.env.user
        printer = user.printing_printer_id or printer_obj.get_default()
        tray = str(user.printer_tray_id.system_name) if user.printer_tray_id else False
        if not printer:
            message = "No printer configured to print %s" % self.name
            user.notify_warning(message=message, title="Print Attachment", sticky=False)
            return {}

        attachment = self.env['ir.attachment'].search(
            [('mimetype', '=', 'application/pdf'),
             ('res_model', '=', 'product.product'),
             ('priority', '>', 0),
             ('res_id', '=', self.product_id.id)],
            order='priority desc, name', limit=1)
        if not attachment:
            attachment = self.env['ir.attachment'].search(
                [('mimetype', '=', 'application/pdf'),
                 ('res_model', '=', 'product.template'),
                 ('priority', '>', 0),
                 ('res_id', '=', self.product_id.product_tmpl_id.id)],
                order='priority desc, name', limit=1)
        if not attachment:
            message = "No prioritized attachment found for product %s" % self.product_id.display_name
            user.notify_warning(message=message, title="Print Attachment", sticky=False)
            return {}

        with open(attachment._full_path(attachment.store_fname), 'rb') as f:
            printer.print_document(
                self,
                f.read(),
                doc_format='pdf',
                action='print',
                # tray=tray,
                tray=False,
            )
        message = "Product attachment sent to printer %s" % printer.name
        user.notify_success(message=message, title="Print Attachment", sticky=False)
        return {}

    @api.multi
    def _generate_moves(self):
        res = super(MrpProduction, self)._generate_moves()
        for production in self:
            bom_lines = self.get_bom_lines(production.product_qty, production.bom_id.id)
            bom_history_lines = []
            for line in bom_lines:
                bom_history_lines.append((0, 0, {'sequence': line[0], 'product_id': line[1], 'product_qty': line[6]}))
            self.env['mrp.bom.history'].create({'mrp_production_id': production.id, 'bom_id': production.bom_id.id,
                                                'bom_history_line_ids': bom_history_lines})
        return res

    def get_bom_lines(self, quantity, bom_id):
        self._cr.execute("""
            with recursive bom_tree (parent_prod_id, comp_prod_id, level, name_path, bom_id, bom_line_id, bom_type, qty) as (
            select
                b.product_id as parent_id,
                l.product_id as comp_id,
                0 as level,
                coalesce(pp.default_code, t.name, '') as name_path,
                b.id as bom_id,
                l.id as line_id,
                b.type as bom_type,
                (l.product_qty * %s) as qty
            from mrp_bom_line as l
            left join mrp_bom as b on b.id=l.bom_id
            left join product_product as pp on pp.id=l.product_id
            left join product_template as t on t.id=pp.product_tmpl_id
            where bom_id= %s
            union select
                b.product_id as parent_id,
                l.product_id as comp_id,
                p.level + 1 as level,
                p.name_path || ' | ' || coalesce(pp.default_code, t.name, '') as name_path,
                b.id as bom_id,
                l.id as line_id,
                b.type as bom_type,
                (p.qty * l.product_qty)
            from mrp_bom_line as l
            left join (
                select distinct on (product_id)
                id,
                product_tmpl_id,
                product_id,
                type
                from mrp_bom
                where active=true
                order by product_id, sequence
            ) as b on b.id=l.bom_id
            left join product_product as pp on pp.id=l.product_id
            left join product_template as t on t.id=pp.product_tmpl_id
            inner join bom_tree as p on b.product_id=p.comp_prod_id
            )
            select
                level,
                comp_prod_id,
                bom_id,
                bom_type,
                bom_line_id,
                name_path,
                qty
    
            from bom_tree as t
            left join mrp_bom as b on b.id = t.bom_id
            order by name_path
        """, (quantity, bom_id)
        )
        return self._cr.fetchall()