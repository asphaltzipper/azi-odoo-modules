from datetime import datetime
from odoo import api, models, _
import logging
logger = logging.getLogger(__name__)


class ReportCombinedBOM(models.AbstractModel):
    _name = 'report.serial_crm.report_combined_bom'
    _description = 'CS Combined BOM'

    @api.model
    def get_html(self, lot_id=False):
        res = self._get_report_data(lot_id)
        return res

    def get_current_bom(self, product_id, bom):
        self._cr.execute("""
            select
                mbl.id as mbl_id,
                mbl.product_id,
                mbl.product_qty,
                mbl.bom_id,
                uu.name ->>'en_US' as uom_name,
                dcb.id as child_bom_id,
                dcb.type
            from mrp_bom_line as mbl
            left join mrp_bom as mb on mb.id=mbl.bom_id
            left join mrp_bom_line_product_template_attribute_value_rel as mblpavr
                on mblpavr.mrp_bom_line_id=mbl.id
            left join product_variant_combination as pavppr
                on pavppr.product_template_attribute_value_id=mblpavr.product_template_attribute_value_id
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
            and ((mb.config_ok=false or mb.config_ok is null) or
                (mb.config_ok=true and pavppr.product_product_id is not null)) 
            group by mbl.id, uu.name, dcb.id, dcb.type, cp.default_code
            order by coalesce(cp.default_code, string_agg(ct.name->> %s, ', '))
        """, (product_id, bom, self.env.lang))
        return self._cr.fetchall()

    def get_mo_child(self, move_line, level=0, repair=False):
        move_data = []
        mo_lines = move_line.consume_line_ids
        level += 1
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
            has_child = self.get_child_mo(line)
            if repair:
                move_data.append([False, line.id, line.lot_id.id, line.display_name, '',  line.product_id.id, line.qty_done,
                                  line.lot_id.name, reference.id, reference and reference.name or '', has_child, '',
                                  line.product_id.display_name, line._name, level])
            else:
                move_data.append([line.id, has_child, line.product_id.id, line.product_id.display_name, line.qty_done,
                                  line.lot_id.name, reference.id, reference and reference.name or '', level])
            if has_child:
                mo_children = self.get_mo_child(line, level)
                move_data.extend(mo_children)
        return move_data

    def get_mo_data(self, move_lines, level=0):
        moves = []
        for line in move_lines:
            has_consume_line = line.consume_line_ids and True or False
            moves.append([line.id, has_consume_line, line.product_id.id, line.product_id.display_name, line.qty_done,
                          line.lot_id.name, line.move_id.production_id.id, line.move_id.production_id.name, level])
            if has_consume_line:
                mo_children = self.get_mo_child(line, level)
                moves.extend(mo_children)
        return moves

    @api.model
    def _get_report_data(self, lot_id):
        lot = self.env['stock.lot'].browse(lot_id)
        move_lines = lot.move_line_ids.filtered(lambda l: l.move_id.production_id)
        mos = self.get_mo_data(move_lines)
        bom_changes = self._get_bom_change_child(lot_id)
        repair_orders = self._get_repair_parts(lot_id)
        return {
            'bom_changes': bom_changes,
            'repair_orders': repair_orders,
            'mo': mos,
        }

    def get_bom_change_children(self, lot_id):
        self._cr.execute("""
            SELECT l.product_id, l.bom_qty, l.component_lot_id, l.change_type, 
                   l.change_date, l.has_child, c.name, l.id 
            FROM stock_lot_change AS l 
            LEFT JOIN stock_lot AS c ON l.component_lot_id = c.id 
            WHERE parent_lot_id = %s
        """, (lot_id,))
        return self._cr.fetchall()

    def get_product_name(self, product_id):
        return self.env['product.product'].browse(product_id).display_name

    def _get_bom_change_hierarchy(self, lot_id, level=0):
        bom_change_with_level = []
        bom_changes = self.get_bom_change_children(lot_id)
        for change in bom_changes:
            product_name = self.get_product_name(change[0])
            bom_change_with_level.append([
                change[0], change[1], change[2], change[3], change[4],
                change[5], change[6], change[7], product_name, level
            ])

            if change[3] == 'add' and change[5]:
                child_changes = self._get_bom_change_hierarchy(change[2], level + 1)
                bom_change_with_level.extend(child_changes)

        return bom_change_with_level

    def _get_bom_change_child(self, lot_id, level=0):
        change_bom = []
        for change in self.env['stock.lot.change'].search([('parent_lot_id', '=', lot_id)]):
            change_bom.append([change.product_id.id, change.bom_qty,  change.component_lot_id.id or '', change.change_type,
                           change.change_date, change.has_child, change.component_lot_id.name, change.id,
                           change.product_id.display_name, level])
            if change.has_child:
                bom_change_child = self._get_bom_change_hierarchy(change.component_lot_id.id, level+1)
                change_bom.extend(bom_change_child)

        return change_bom

    def get_repair_bom(self, product, level=0, include_bom=False):
        repair_bom_lines = []
        level += 1
        bom = self.env['mrp.bom'].search([('product_id', '=', product.id)], order='version desc, sequence', limit=1)
        if bom:
            child_boms = self.get_current_bom(bom.product_id.id, bom.id)
            if include_bom:
                repair_bom_lines.append([True, bom.id, bom.product_id.id, bom.product_id.display_name, bom.product_qty,
                                         False, False, bom._name, level])
                level = 1.2
            for child in child_boms:
                product = self.env['product.product'].browse(child[1])
                product_name = product.display_name
                repair_bom_lines.append([True, child[3], child[1], product_name, child[2], child[5], child[6],
                                         bom._name, level])
                if child[5]:
                    bom_children = self.get_repair_bom(product, level+1)
                    repair_bom_lines.extend(bom_children)
        return repair_bom_lines

    def get_repair_mo(self, move_lines, level=1):
        mo_lines = []
        for line in move_lines:
            has_child = line.consume_line_ids and True or False
            mo_lines.append([False, line.id, line.lot_id.id, line.display_name, '', line.product_id.id,
                             line.qty_done, line.lot_id.name, line.move_id.production_id.id,
                             line.move_id.production_id.name, has_child,
                             line.date, line.product_id.display_name, line.move_id.production_id._name, level])
            if has_child:
                mo_child = self.get_mo_child(line, level, True)
                mo_lines.extend(mo_child)
        return mo_lines

    def get_repair_children(self, lot=False, product_id=False):
        repair_children = []
        move_lines = lot and lot.move_line_ids.filtered(lambda l: l.move_id.production_id)
        move_lines = move_lines and move_lines[0]
        if not move_lines and product_id:
            bom = self.get_repair_bom(product_id, include_bom=True)
            if bom:
                repair_children.extend(bom)
        if move_lines:
            repair_children.extend(self.get_repair_mo(move_lines))
        return repair_children

    def _get_repair_parts(self, lot_id):
        repairs = []
        repair_lines = self.env['repair.line'].search([('repair_id.lot_id', '=', lot_id)])
        for line in repair_lines:
            repairs.append([False, line.id, line.lot_id.id, line.name, line.type, line.product_id.id,
                            line.product_uom_qty, line.lot_id.name, line.repair_id.id, line.repair_id.name,
                            line.has_child, line.create_date, line.product_id.display_name, line._name])
            if line.has_child:
                children = self.get_repair_children(line.lot_id, line.product_id)
                repairs.extend(children)

        return repairs

    def get_child_mo(self, move_line):
        mo_lines = False
        if move_line.lot_id:
            mrp = move_line.lot_id.move_line_ids.filtered(lambda l: l.move_id.production_id)
            if mrp:
                mo_lines = True
        return mo_lines
