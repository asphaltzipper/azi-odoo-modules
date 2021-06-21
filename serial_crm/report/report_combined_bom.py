from odoo import api, models, _


class ReportCombinedBOM(models.AbstractModel):
    _name = 'report.serial_crm.report_combined_bom'
    _description = 'CS Combined BOM'

    @api.model
    def get_html(self, lot_id=False):
        res = self._get_report_data(lot_id)
        res['lines'] = self.env.ref('serial_crm.report_combined_bom').render({'data': res['lines']})
        return res

    @api.model
    def _get_report_data(self, lot_id):
        lot = self.env['stock.production.lot'].browse(lot_id)
        production_id = lot.move_line_ids.mapped('move_id.production_id')
        lines = []
        if production_id:
            lines = self._get_line(lot)
        return {
            'lines': lines,
        }

    def _get_line(self, lot=False):
        lines = []
        for l in lot:
            reference = l.repair_ids and l.repair_ids.mapped('name')[0] or False
            repair = l.repair_ids and l.repair_ids.mapped('id')[0] or False
            if l.change_ids:
                reference = 'ADD'
            lines.append({
                'reference': reference,
                'repair': repair,
                'product': l.product_id,
                'date': l.move_line_ids.mapped('date')[0],
                'lot': l,
                'quantity': l.product_qty,
            })
        return lines
