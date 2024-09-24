from odoo import api, models
import re


class ReportBomStructure(models.AbstractModel):
    _name = 'report.azi_stock.report_serial_plc_label'
    _description = 'PLC Label'

    def get_note_values(self, lot):
        label_re = re.compile(r'(PROGRAM)[\r\n]+DESC\:\W*(.*)[\r\n]+CONFIG\:\W*(.+)')
        notes = lot.note_ids.filtered(lambda x: 'PROGRAM' in x.name)
        code_match = False
        res = (False, False)
        for note in notes.sorted(key=lambda r: r.create_date, reverse=True):
            code_match = label_re.match(note.name or '')
            if code_match and len(code_match.groups()) == 3:
                res = (code_match.group(2), code_match.group(3))
                break
        doc = {
            'lot': lot,
            'id': lot.id,
            'serial': lot.name,
            'desc': res and res[0] or False,
            'config': res and res[1] or '',
        }
        return doc


    @api.model
    def _get_report_values(self, docids, data=None):
        return {
            'doc_ids': docids,
            'doc_model': 'stock.lot',
            'docs': self.env['stock.lot'].browse(docids),
            'get_note_values': self.get_note_values,
        }
