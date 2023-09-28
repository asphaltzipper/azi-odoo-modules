# -*- coding: utf-8 -*-

import base64
import csv

from odoo import api, models, fields, _
from odoo.exceptions import UserError


class MfgWorkImport(models.TransientModel):
    _name = 'mfg.work.import'
    _description = 'Import Manufacturing Work Data'

    data_file = fields.Binary(
        string='Manufacturing Work Data File',
        required=True,
        help='Must be CSV format (delimiter=","), with no header row.\n'
             'Columns:\n'
             ' - Product Mfg Code\n'
             ' - Manufacturing Order Name/Number\n'
             ' - Completed Quantity')

    filename = fields.Char(
        string="Filename")

    header_id = fields.Many2one(
        comodel_name='mfg.work.header',
        string="MFG Work Import Header",
        readonly=True,
        required=True,
        ondelete='cascade')

    @api.model
    def default_get(self, fields):
        res = super(MfgWorkImport, self).default_get(fields)
        res['header_id'] = self._context['active_id']
        return res

    def action_import(self):
        """Load manufacturing work data from the CSV file."""

        product_obj = self.env['product.product']
        work_detail_obj = self.env['mfg.work.detail']

        # Decode the file data
        data = base64.b64decode(self.data_file)
        reader = csv.reader((data.decode()).splitlines())
        reader_info = []
        try:
            reader_info.extend(reader)
        except Exception:
            raise UserError(_("Not a valid file!"))

        # import detail records
        keys = ['import_mfg_code', 'import_production_code', 'import_quantity']
        for i in range(len(reader_info)):
            row = reader_info[i]
            if not len(row) == 3:
                raise UserError("Bad row in file")
                # continue
            values = dict(zip(keys, row))
            product = product_obj.search([('mfg_code', '=', values['import_mfg_code'])])
            if len(product) > 1:
                continue
            values.update({
                'header_id': self.header_id.id,
                'product_id': product.id or False,
                'actual_quantity': values['import_quantity'],
            })
            work_detail_obj.create(values)

        self.header_id.file_name = self.filename
        self.header_id.name = self.filename
        self.header_id.state = 'imported'
        return {}
