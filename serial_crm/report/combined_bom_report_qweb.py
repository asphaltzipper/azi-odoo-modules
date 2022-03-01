import calendar

from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CombinedBOMReport(models.AbstractModel):
    _name = 'report.serial_crm.combined_bom'
    _description = 'Combined BOM (HTML)'

    def get_bom_change(self, lot_id):
        self._cr.execute("""select l.product_id, l.bom_qty, l.component_lot_id, l.change_type, l.change_date,
                l.has_child, c.name, l.id from stock_lot_change as l left join stock_production_lot as c 
                on l.component_lot_id = c.id
                where parent_lot_id = %s""", (lot_id,))
        return self._cr.fetchall()

    def get_change_child(self, has_child, component_lot_id, level, child=[]):
        while has_child:
            level += 1
            bom_changes = self.get_bom_change(component_lot_id)
            for change in bom_changes:
                child.append([change[0], change[1], change[2], change[3],
                              change[4], change[5], change[6], change[7], level])
                if change[3] == 'add' and change[5]:
                    self.get_change_child(change[5], change[2], level, child)
            has_child = False
        return child

    def _get_bom_change_child(self, lot_id):
        bom_change_with_level = []
        bom_changes = self.get_bom_change(lot_id)
        for change in bom_changes:
            level = 0
            child = []
            bom_change_with_level.append([change[0], change[1], change[2], change[3],
                                          change[4], change[5], change[6], change[7], level])
            if change[3] == 'add' and change[5]:
                child = self.get_change_child(change[5], change[2], level, child)
            bom_change_with_level.extend(child)
        return bom_change_with_level

    def get_current_bom(self, product_id, bom):
        self._cr.execute("""
            select
                mbl.id as mbl_id,
                mbl.product_id,
                mbl.product_qty,
                mbl.bom_id,
                uu.name as uom_name,
                dcb.id as child_bom_id,
                dcb.type
            from mrp_bom_line as mbl
            left join mrp_bom as mb on mb.id=mbl.bom_id
            left join mrp_bom_line_product_attribute_value_rel as mblpavr
                on mblpavr.mrp_bom_line_id=mbl.id
            left join product_attribute_value_product_product_rel as pavppr
                on pavppr.product_attribute_value_id=mblpavr.product_attribute_value_id
                and pavppr.product_product_id=%s
            left join product_product as cp on cp.id=mbl.product_id
            left join product_template as ct on ct.id=cp.product_tmpl_id
            left join uom_uom as uu on uu.id=ct.uom_id
            left join (
                select distinct on (product_tmpl_id) *
                from mrp_bom
                where active=true
                order by product_tmpl_id, version desc, sequence
            ) as dcb on dcb.product_tmpl_id=cp.product_tmpl_id
            where mbl.bom_id=%s
            and (mb.config_ok=false or
                (mb.config_ok=true and pavppr.product_product_id is not null))
            order by coalesce(cp.default_code, ct.name)
        """, (product_id, bom,))
        return self._cr.fetchall()

    def get_child_bom(self, product_id, bom_id, level, child=[]):
        if bom_id:
            level += 1
            boms = self.get_current_bom(product_id, bom_id)
            for bom in boms:
                child.append([bom[0], bom[1], bom[2], bom[3], bom[4], bom[5], bom[6], level])
                if bom[5]:
                    self.get_child_bom(bom[1], bom[5], level, child)
        return child

    def get_all_current_bom(self, product_id, bom_id, level=1):
        current_boms = []
        boms = self.get_current_bom(product_id, bom_id)
        for bom in boms:
            child = []
            current_boms.append([bom[0], bom[1], bom[2], bom[3], bom[4], bom[5], bom[6], level])
            if bom[5]:
                child = self.get_child_bom(bom[1], bom[5], level, child)
            current_boms.extend(child)
        return current_boms

    def get_mo_child(self, move_line_id, level=0, move_data=[], repair=False):
        mo_lines = move_line_id.consume_line_ids
        if not mo_lines:
            if move_line_id.move_id.move_orig_ids:
                mo_lines = move_line_id.move_id.move_orig_ids.mapped('move_line_ids').filtered(
                    lambda m: m.lot_id == move_line_id.lot_id and m.state == 'done'
                )
        if not mo_lines and move_line_id.lot_id:
            mrp_production = move_line_id.lot_id.move_line_ids.filtered(lambda l: l.move_id.production_id)
            if mrp_production:
                mo_lines = mrp_production[0].consume_line_ids
        level += 1
        for line in mo_lines:
            reference = line.move_id.production_id and line.move_id.production_id or \
                        (line.move_id.raw_material_production_id and line.move_id.raw_material_production_id)

            move_data.append([line.id, level, line.product_id.id, line.qty_done,
                              line.lot_id.name, reference.display_name, line.product_id.display_name, move_line_id])
            lot_move = line.lot_id.move_line_ids.filtered(lambda l: l.move_id.production_id)
            if lot_move:
                self.get_mo_child(lot_move[0], level, move_data)
        return move_data

    def _get_repair_parts(self, lot_id):
        self._cr.execute("""select 
        l.type, l.product_id, l.product_uom_qty, p.name, r.name, l.create_date, l.lot_id
        from repair_line as l 
        left join repair_order as r on l.repair_id = r.id 
        left join stock_production_lot as p on  l.lot_id = p.id
        where r.lot_id =%s
        """, (lot_id,))
        return self._cr.fetchall()

    def get_repair_with_child(self, lot_id):
        repair_parts = []
        repair_orders = self._get_repair_parts(lot_id)
        level = 0
        for order in repair_orders:
            repair_parts.append([order[0], order[1], order[2], order[3], order[4], order[5], level])
            is_move = False
            if order[6]:
                # get mo related to parts
                lot = self.env['stock.production.lot'].browse(order[6])
                move_lines = lot.move_line_ids.filtered(lambda l: l.move_id.production_id)
                if move_lines:
                    is_move = True
                    move_line = move_lines[0]
                    reference = move_line.move_id.production_id and move_line.move_id.production_id.display_name or \
                                (move_line.move_id.raw_material_production_id and
                                 move_line.move_id.raw_material_production_id.display_name)
                    repair_parts.append(['', move_line.product_id.id, move_line.qty_done, move_line.lot_id.display_name,
                                         reference, move_line.date, level + 1])
                    mo_children = self.get_mo_child(move_line, 1, [])
                    for child in mo_children:
                        repair_parts.append(['', child[2], child[3], child[4], child[5], '', child[1]])
            if not is_move:
                bom = self.env['mrp.bom'].search([('product_id', '=', order[1])], order='version, sequence', limit=1)
                if bom:
                    repair_parts.append(['', bom.product_id.id, bom.product_qty, '', bom.display_name, '', level + 1])
                    child_boms = self.get_all_current_bom(bom.product_id.id, bom.id, level=2)
                    for b in child_boms:
                        product = self.env['product.product'].browse(b[1])
                        repair_parts.append(['', b[1], b[2], '', product.display_name, '', b[7]])
        return repair_parts

    @api.model
    def _get_report_values(self, docids, data=None):
        assert len(docids) == 1, "Please select one lot"
        bom_report = self.env['ir.actions.report']._get_report_from_name('serial_crm.combined_bom')
        lots = self.env['stock.production.lot'].browse(docids)
        bom_lines = []
        current_boms = lots.product_id.bom_ids
        current_bom = self.env['mrp.bom']
        if current_boms:
            current_bom = self.env['mrp.bom'].search([('id', 'in', current_boms.ids)], order='version, sequence',
                                                     limit=1)
            if current_bom:
                bom_lines = self.get_all_current_bom(current_bom.product_id.id, current_bom.id)
        move_lines = lots.move_line_ids.filtered(lambda l: l.move_id.production_id)
        mo_children = []
        if move_lines:
            mo_children = self.get_mo_child(move_lines[0])
        return {
            'doc_ids': self.ids,
            'doc_model': bom_report.model,
            'docs': lots,
            'bom_changes': self._get_bom_change_child(lots.id),
            'bom_lines': bom_lines,
            'current_bom': current_bom,
            'mo_children': mo_children,
            'mo': move_lines and move_lines[0],
            'repair_orders': self.get_repair_with_child(lots.id),
        }
