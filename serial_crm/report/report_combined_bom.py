from odoo import api, models, _


class ReportCombinedBOM(models.AbstractModel):
    _name = 'report.serial_crm.report_combined_bom'
    _description = 'CS Combined BOM'

    @api.model
    def get_html(self, lot_id=False):
        res = self._get_report_data(lot_id)
        res['lines'] = self.env.ref('serial_crm.report_combined_bom').render({'data': res})
        return res

    @api.model
    def _get_report_data(self, lot_id):
        lot = self.env['stock.production.lot'].browse(lot_id)
        move_lines = lot.move_line_ids.filtered(lambda l: l.move_id.production_id)
        lines = []
        bom_changes = self._get_bom_change_child(lot_id)
        repair_orders = self._get_repair_parts(lot_id)
        return {
            'lines': lines,
            'bom_changes': bom_changes,
            'repair_orders': repair_orders,
            'get_product_display_name': self.get_product_display_name,
            'mo': move_lines,
            'mo_lot': lot.name,
        }

    def _get_bom_change_child(self, lot_id):
        self._cr.execute("""select l.product_id, l.bom_qty, l.component_lot_id, l.change_type, l.change_date,
                l.has_child, c.name, l.id from stock_lot_change as l left join stock_production_lot as c 
                on l.component_lot_id = c.id
                where parent_lot_id = %s""", (lot_id,))
        return self._cr.fetchall()

    def _get_repair_parts(self, lot_id):
        self._cr.execute("""select 
        l.id, l.lot_id, l.name, l.type, l.product_id, l.product_uom_qty, p.name, l.repair_id, r.name, l.has_child, 
        l.create_date
        from repair_line as l 
        left join repair_order as r on l.repair_id = r.id 
        left join stock_production_lot as p on  l.lot_id = p.id
        where r.lot_id =%s
        """, (lot_id,))
        return self._cr.fetchall()

    def get_product_display_name(self, product_id):
        return self.env['product.product'].browse(product_id).display_name

    def get_child_mo(self, move_line):
        mo_lines = move_line.consume_line_ids
        if not mo_lines:
            if move_line.move_id.move_orig_ids:
                mo_lines = move_line.move_id.move_orig_ids.mapped('move_line_ids').filtered(
                    lambda m: m.lot_id == move_line.lot_id and m.state == 'done'
                )
        return mo_lines and True or False

    @api.model
    def get_mo_component(self, move_line_id, level=False):
        move_line = self.env['stock.move.line'].browse(move_line_id)
        move_data = []
        mo_lines = move_line.consume_line_ids
        if not mo_lines:
            if move_line.move_id.move_orig_ids:
                mo_lines = move_line.move_id.move_orig_ids.mapped('move_line_ids').filtered(
                    lambda m: m.lot_id == move_line.lot_id and m.state == 'done'
                )
        for line in mo_lines:
            reference = line.move_id.production_id and line.move_id.production_id or \
                        (line.move_id.raw_material_production_id and line.move_id.raw_material_production_id)

            move_data.append({
                'id': line.id,
                'level': level,
                'has_child': self.get_child_mo(line),
                'product_id': line.product_id,
                'product_qty': line.qty_done,
                'lot_name': line.lot_id.name,
                'reference': reference,
                'parent': move_line_id,
            })
        lines = {
            'mo_lines': move_data,
        }
        return self.env.ref('serial_crm.report_mrp_order_line').render({'data': lines})

    @api.model
    def get_bom_change(self, bom_change_id=False, bom_child_component_id=False, level=False):
        change_line = self._get_bom_change_child(bom_child_component_id)
        lines = {
            'change_line': change_line,
            'parent': bom_change_id,
            'get_product_display_name': self.get_product_display_name,
            'level': level or 0,

        }
        return self.env.ref('serial_crm.report_bom_change_line').render({'data': lines})

    @api.model
    def get_repair_order(self, repair_lot_id=False, line_id=False, level=False):
        repair_parts = self._get_repair_parts(repair_lot_id)
        lines = {
            'repair_line': repair_parts,
            'parent': line_id,
            'level': level or 0,
        }
        return self.env.ref('serial_crm.report_repair_order_line').render({'data': lines})