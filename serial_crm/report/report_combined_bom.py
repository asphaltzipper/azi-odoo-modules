from datetime import datetime
from odoo import api, models, _


class ReportCombinedBOM(models.AbstractModel):
    _name = 'report.serial_crm.report_combined_bom'
    _description = 'CS Combined BOM'

    @api.model
    def get_html(self, lot_id=False):
        res = self._get_report_data(lot_id)
        res['lines'] = self.env.ref('serial_crm.report_combined_bom').render({'data': res})
        return res

    def get_current_bom(self, bom):
        self._cr.execute("""
            select 
                line.id, line.product_id, line.product_qty, line.bom_id, uom.name,
                (case 
                    when bom.product_id = line.product_id then True
                    else False
                end) as child_bom_id, bom.type
            from mrp_bom_line as line
            left join mrp_bom as bom  on line.product_id  =  bom.product_id 
            left join uom_uom as uom on line.product_uom_id = uom.id
            where line.bom_id = %s
            group by line.id, bom.product_id, uom.name, bom.type
        """, (bom,))
        return self._cr.fetchall()

    def get_bom_id(self, product):
        self._cr.execute("""
            select bom.id 
            from mrp_bom as bom, mrp_bom_line as line 
            where bom.product_id = %s and bom.id = line.bom_id limit 1""", (product,))
        return self._cr.fetchall()[0][0]

    @api.model
    def _get_report_data(self, lot_id):
        lot = self.env['stock.production.lot'].browse(lot_id)
        move_lines = lot.move_line_ids.filtered(lambda l: l.move_id.production_id)
        lines = []
        bom_lines = []
        bom_changes = self._get_bom_change_child(lot_id)
        repair_orders = self._get_repair_parts(lot_id)
        current_boms = lot.product_id.bom_ids
        if current_boms:
            current_bom = self.env['mrp.bom'].search([('id', 'in', current_boms.ids)], order='version desc, sequence', limit=1)
            if current_bom:
                bom_lines = self.get_current_bom(current_bom.id)
        return {
            'lines': lines,
            'bom_changes': bom_changes,
            'repair_orders': repair_orders,
            'get_product_display_name': self.get_product_display_name,
            'bom_lines': bom_lines,
            'get_bom_id': self.get_bom_id,
            'mo': move_lines,
            'mo_lot': lot.name,
            'current_bom': current_bom,
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
        mo_lines = False
        if move_line.lot_id:
            mrp = move_line.lot_id.move_line_ids.filtered(lambda l: l.move_id.production_id)
            if mrp:
                mo_lines = True
        return mo_lines

    @api.model
    def get_mo_component(self, move_line_id, level=False, repair=False):
        if type(move_line_id) == str and move_line_id.startswith('r_'):
            move_line_id = move_line_id[2:]
        move_line = self.env['stock.move.line'].browse(int(move_line_id))
        move_data = []
        mo_lines = move_line.consume_line_ids
        if repair:
            level = level and level + 1 or 0
        if not mo_lines:
            if move_line.move_id.move_orig_ids:
                mo_lines = move_line.move_id.move_orig_ids.mapped('move_line_ids').filtered(
                    lambda m: m.lot_id == move_line.lot_id and m.state == 'done'
                )
        if not mo_lines and move_line.lot_id:
            mrp_production = move_line.lot_id.move_line_ids.filtered(lambda l: l.move_id.production_id)
            if mrp_production:
                mo_lines = mrp_production[0].consume_line_ids
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
            'repair': bool(repair),
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
    def get_bom_line(self, bom_line_id=False, level=False, bom_child=False, repair=False):
        bom_line_child = self.get_current_bom(bom_child)
        if repair:
            level = level and level + 1
        lines = {
            'bom_child': bom_line_child,
            'parent_id': bom_line_id,
            'level': level or 0,
            'repair': bool(repair),
            'get_bom_id': self.get_bom_id,
            'get_product_display_name': self.get_product_display_name,
        }
        return self.env.ref('serial_crm.report_bom_child_line').render({'data': lines})

    @api.model
    def get_repair_order(self, repair_lot_id=False, line_id=False, level=False, product_id=False):
        move_lines = self.env['stock.move.line']
        bom = self.env['mrp.bom']
        if repair_lot_id:
            lot = self.env['stock.production.lot'].browse(repair_lot_id)
            move_lines = lot.move_line_ids.filtered(lambda l: l.move_id.production_id)
            move_lines = move_lines and move_lines[0]
        if not move_lines and product_id:
            bom = self.env['mrp.bom'].search([('product_id', '=', product_id)], order='version desc, sequence', limit=1)
        child_boms = []
        if bom:
            child_boms = self.get_current_bom(bom.id)
        lines = {
            'boms': bom,
            'child_boms': child_boms,
            'parent': line_id,
            'level': level or 0,
            'mrp': move_lines,
            'repair': True,
            'get_bom_id': self.get_bom_id,
            'get_product_display_name': self.get_product_display_name,
        }
        return self.env.ref('serial_crm.report_repair_order_line').render({'data': lines})
