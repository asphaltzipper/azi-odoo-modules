# -*- coding: utf-8 -*-
import datetime
import base64
from io import BytesIO
from PyPDF2 import PdfFileReader, PdfFileWriter


from odoo import fields, models, api, Command


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    @api.model
    def _get_default_date_planned_start(self):
        if self.env.context.get('default_date_deadline'):
            return fields.Datetime.to_datetime(self.env.context.get('default_date_deadline'))
        return datetime.datetime.now()

    date_planned_start = fields.Datetime(
        string='Scheduled Date',
        copy=False,
        default=_get_default_date_planned_start,
        index=True,
        required=True,
        help="Date at which you plan to start the production.",
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

    @api.depends('bom_id', 'product_id', 'product_qty', 'product_uom_id')
    def _compute_workorder_ids(self):
        for production in self:
            if production.state != 'draft':
                continue
            workorders_list = [Command.link(wo.id) for wo in
                               production.workorder_ids.filtered(lambda wo: not wo.operation_id)]
            workorders_list += [Command.delete(wo.id) for wo in production.workorder_ids.filtered(
                lambda wo: wo.operation_id and wo.operation_id.bom_id != production.bom_id)]
            if not production.bom_id and not production._origin.product_id:
                production.workorder_ids = workorders_list
            if production.product_id != production._origin.product_id:
                production.workorder_ids = [Command.clear()]
            if production.bom_id and production.product_id and production.product_qty > 0:
                # keep manual entries
                workorders_values = []
                product_qty = production.product_uom_id._compute_quantity(production.product_qty,
                                                                          production.bom_id.product_uom_id)
                exploded_boms, dummy = production.bom_id.explode(production.product_id,
                                                                 product_qty / production.bom_id.product_qty,
                                                                 picking_type=production.bom_id.picking_type_id)

                new_exploded_boms = [(bom, _) for bom, _ in exploded_boms[1:] if bom.type != 'phantom']
                exploded_boms = [exploded_boms[0]] + new_exploded_boms
                for bom, bom_data in exploded_boms:
                    # If the operations of the parent BoM and phantom BoM are the same, don't recreate work orders.
                    if not (bom.operation_ids and (not bom_data['parent_line'] or bom_data[
                        'parent_line'].bom_id.operation_ids != bom.operation_ids)):
                        continue
                    for operation in bom.operation_ids:
                        if operation._skip_operation_line(bom_data['product']):
                            continue
                        workorders_values += [{
                            'name': operation.name,
                            'production_id': production.id,
                            'workcenter_id': operation.workcenter_id.id,
                            'product_uom_id': production.product_uom_id.id,
                            'operation_id': operation.id,
                            'state': 'pending',
                        }]
                workorders_dict = {wo.operation_id.id: wo for wo in
                                   production.workorder_ids.filtered(lambda wo: wo.operation_id)}
                for workorder_values in workorders_values:
                    if workorder_values['operation_id'] in workorders_dict:
                        # update existing entries
                        workorders_list += [
                            Command.update(workorders_dict[workorder_values['operation_id']].id, workorder_values)]
                    else:
                        # add new entries
                        workorders_list += [Command.create(workorder_values)]
                production.workorder_ids = workorders_list
            else:
                production.workorder_ids = [Command.delete(wo.id) for wo in
                                            production.workorder_ids.filtered(lambda wo: wo.operation_id)]

    def write(self, vals):
        """Override write method to update stock move expected date that is related to mrp production"""
        res = super(MrpProduction, self).write(vals)
        if 'date_planned_finished' in vals or 'date_planned_start' in vals:
            for record in self:
                date_planned_start = 'date_planned_start' in vals and vals[
                    'date_planned_start'] or record.date_planned_start
                moves = self.env['stock.move'].search(['|', ('raw_material_production_id', '=', record.id),
                                                       ('production_id', '=', record.id),
                                                       ('state', 'not in', ('cancel', 'done'))])
                moves.sudo().write({'date_deadline': date_planned_start,
                                    'date': date_planned_start})
                move_lines = moves.mapped('move_line_ids')
                move_lines and move_lines.sudo().write({'date': date_planned_start})
        return res

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
        report_bytes, _ = report._render_qweb_pdf('azi_mrp.action_report_production_order_azi', res_ids=self.id)
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

    def direct_print_azi_report(self):
        self.ensure_one()
        report = self.env['ir.actions.report']._get_report_from_name('azi_mrp.report_mrporder_azi')
        report_bytes, _ = report._render_qweb_pdf('azi_mrp.action_report_production_order_azi', res_ids=self.id)
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
