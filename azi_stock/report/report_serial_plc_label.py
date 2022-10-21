from odoo import api, models
import re


class ReportBomStructure(models.AbstractModel):
    _name = 'report.azi_stock.report_serial_plc_label'
    _description = 'PLC Label'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = []
        label_re = re.compile(r'(PROGRAM)[\r\n]+DESC\:\W*(.*)[\r\n]+CONFIG\:\W*(.+)')
        for lot_id in docids:
            lot = self.env['stock.production.lot'].browse(lot_id)
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
                'id': lot_id,
                'serial': lot.name,
                'desc': res and res[0] or False,
                'config': res and res[1] or False,
            }
            docs.append(doc)
        return {
            'doc_ids': docids,
            'doc_model': 'stock.production.lot',
            'docs': docs,
        }
