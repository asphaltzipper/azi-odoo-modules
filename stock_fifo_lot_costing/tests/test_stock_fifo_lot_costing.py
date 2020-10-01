# Copyright 2020 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from .test_stock_fifo_lot_costing_common import TestStockFifoLotCostingCase


class TestStockFifoLotCosting(TestStockFifoLotCostingCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_inbound_line_remaining(self):
        """Create inbound product move, with serial tracking, and verify
         stock.move.line.remaining_qty"""
        self.prod_1.standard_price = 10.0
        line_data = {
            'product_qty': 1.0,
            'location_id': self.stock_loc.id,
            'product_id': self.prod_1.id,
            'product_uom_id': self.prod_1.uom_id.id,
            'theoretical_qty': 0.0,
            'prod_lot_id': self.prod_1_lot1.id,
        }
        inventory = self.inventory_obj.create({
            'name': 'INV: %s' % self.prod_1.display_name,
            'filter': 'product',
            'product_id': self.prod_1.id,
            'location_id': self.stock_loc.id,
            'line_ids': [(0, 0, line_data)],
        })
        inventory.action_validate()

        self.assertEqual(len(inventory.move_ids), 1)
        self.assertEqual(len(inventory.move_ids.move_line_ids), 1)
        self.assertAlmostEqual(inventory.move_ids.remaining_value, 10.0, 5)
        self.assertAlmostEqual(inventory.move_ids.remaining_qty, 1.0, 5)
        self.assertAlmostEqual(inventory.move_ids.move_line_ids.remaining_qty, 1.0, 5)

        entries = self.entry_obj.search([('stock_move_id', 'in', inventory.move_ids.ids)])
        self.assertEqual(len(entries), 1)
        self.assertEqual(len(entries.line_ids), 2)

        entry_line = entries.line_ids.filtered(
            lambda x: x.account_id == self.account_inv)
        self.assertAlmostEqual(entry_line.debit, 10.0, 2)

    def test_outbound_line_remaining(self):
        """Create outbound product move, with serial tracking, and verify
         stock.move.line.remaining_qty of the original inbound move"""
        self.prod_1.standard_price = 10.0
        line_data = {
            'product_qty': 1.0,
            'location_id': self.stock_loc.id,
            'product_id': self.prod_1.id,
            'product_uom_id': self.prod_1.uom_id.id,
            'theoretical_qty': 0.0,
            'prod_lot_id': self.prod_1_lot1.id,
        }
        inventory_in = self.inventory_obj.create({
            'name': 'INV: %s' % self.prod_1.display_name,
            'filter': 'product',
            'product_id': self.prod_1.id,
            'location_id': self.stock_loc.id,
            'line_ids': [(0, 0, line_data)],
        })
        inventory_in.action_validate()

        self.pick_out_prod_1.move_lines[0].move_line_ids[0].lot_id = self.prod_1_lot1
        self.pick_out_prod_1.move_lines[0].move_line_ids[0].qty_done = 1.0
        self.pick_out_prod_1.action_done()

        self.assertAlmostEqual(inventory_in.move_ids.remaining_value, 0.0, 5)
        self.assertAlmostEqual(inventory_in.move_ids.remaining_qty, 0.0, 5)
        self.assertAlmostEqual(inventory_in.move_ids.move_line_ids.remaining_qty, 0.0, 5)

    def test_outbound_alternate_serial(self):
        """Create outbound product move, with serial tracking, and verify
         stock.move.line.remaining_qty of the original inbound move"""
        self.prod_1.standard_price = 11.0
        line_data = {
            'product_qty': 1.0,
            'location_id': self.stock_loc.id,
            'product_id': self.prod_1.id,
            'product_uom_id': self.prod_1.uom_id.id,
            'theoretical_qty': 0.0,
            'prod_lot_id': self.prod_1_lot1.id,
        }
        inventory_in1 = self.inventory_obj.create({
            'name': 'INV: %s [%s]' % (
                self.prod_1.display_name, self.prod_1_lot1.name),
            'filter': 'product',
            'product_id': self.prod_1.id,
            'location_id': self.stock_loc.id,
            'line_ids': [(0, 0, line_data)],
        })
        inventory_in1.action_validate()

        self.prod_1.standard_price = 12.0
        line_data = {
            'product_qty': 1.0,
            'location_id': self.stock_loc.id,
            'product_id': self.prod_1.id,
            'product_uom_id': self.prod_1.uom_id.id,
            'theoretical_qty': 0.0,
            'prod_lot_id': self.prod_1_lot2.id,
        }
        inventory_in2 = self.inventory_obj.create({
            'name': 'INV: %s [%s]' % (
                self.prod_1.display_name, self.prod_1_lot2.name),
            'filter': 'product',
            'product_id': self.prod_1.id,
            'location_id': self.stock_loc.id,
            'line_ids': [(0, 0, line_data)],
        })
        inventory_in2.action_validate()

        # deliver lot2
        self.pick_out_prod_1.move_lines[0].move_line_ids[0].lot_id = self.prod_1_lot2
        self.pick_out_prod_1.move_lines[0].move_line_ids[0].qty_done = 1.0
        self.pick_out_prod_1.action_done()

        self.assertAlmostEqual(inventory_in1.move_ids.remaining_value, 11.0, 5)
        self.assertAlmostEqual(inventory_in1.move_ids.remaining_qty, 1.0, 5)
        self.assertAlmostEqual(
            inventory_in1.move_ids.move_line_ids.remaining_qty, 1.0, 5)

        self.assertAlmostEqual(inventory_in2.move_ids.remaining_value, 0.0, 5)
        self.assertAlmostEqual(inventory_in2.move_ids.remaining_qty, 0.0, 5)
        self.assertAlmostEqual(
            inventory_in2.move_ids.move_line_ids.remaining_qty, 0.0, 5)

        entries = self.entry_obj.search(
            [('stock_move_id', 'in', self.pick_out_prod_1.move_lines.ids)])
        self.assertEqual(len(entries), 1)
        self.assertEqual(len(entries.line_ids), 2)

        entry_line = entries.line_ids.filtered(
            lambda x: x.account_id == self.account_inv)
        self.assertAlmostEqual(entry_line.credit, 12.0, 2)

    def test_outbound_multi_serial(self):
        """Create outbound product move, with serial tracking, and verify
         stock.move.line.remaining_qty of the original inbound move"""
        self.prod_1.standard_price = 11.0
        inv_line_data = {
            'product_qty': 1.0,
            'location_id': self.stock_loc.id,
            'product_id': self.prod_1.id,
            'product_uom_id': self.prod_1.uom_id.id,
            'theoretical_qty': 0.0,
            'prod_lot_id': self.prod_1_lot1.id,
        }
        inventory_in1 = self.inventory_obj.create({
            'name': 'INV: %s [%s]' % (
                self.prod_1.display_name, self.prod_1_lot1.name),
            'filter': 'product',
            'product_id': self.prod_1.id,
            'location_id': self.stock_loc.id,
            'line_ids': [(0, 0, inv_line_data)],
        })
        inventory_in1.action_validate()

        # receive lot2 and lot3
        pick_in_prod_1 = self.picking_obj.create({
            'location_id': self.supplier_loc.id,
            'location_dest_id': self.stock_loc.id,
            'partner_id': self.partner_supplier.id,
            'picking_type_id': self.wh.in_type_id.id,
        })
        move = self.move_obj.create({
            'picking_id': pick_in_prod_1.id,
            'picking_type_id': self.wh.in_type_id.id,
            'name': self.prod_1.name,
            'product_id': self.prod_1.id,
            'product_uom_qty': 2.0,
            'product_uom': self.prod_1.uom_id.id,
            'location_id': self.supplier_loc.id,
            'location_dest_id': self.stock_loc.id,
            'warehouse_id': self.wh.id,
            'route_ids': [(6, 0, [self.wh.reception_route_id.id])],
            'state': 'draft',
            'quantity_done': 2.0,
            'price_unit': 12.0,
            'value': 24.0,
        })
        move.move_line_ids.unlink()
        move._action_confirm()
        move._action_assign()
        pick_in_prod_1.move_lines[0].move_line_ids[0].write({
            'lot_id': self.prod_1_lot2.id,
            'qty_done': 1.0,
        })
        pick_in_prod_1.move_lines[0].move_line_ids[1].write({
            'lot_id': self.prod_1_lot3.id,
            'qty_done': 1.0,
        })
        pick_in_prod_1.action_done()

        self.assertAlmostEqual(self.prod_1.standard_price, 11.0, 5)
        self.assertAlmostEqual(inventory_in1.move_ids.remaining_value, 11.0, 5)
        self.assertAlmostEqual(inventory_in1.move_ids.remaining_qty, 1.0, 5)
        self.assertAlmostEqual(
            inventory_in1.move_ids.move_line_ids.remaining_qty, 1.0, 5)

        self.assertAlmostEqual(move.remaining_value, 24.0, 5)
        self.assertAlmostEqual(move.remaining_qty, 2.0, 5)
        self.assertAlmostEqual(move.move_line_ids[0].remaining_qty, 1.0, 5)
        self.assertAlmostEqual(move.move_line_ids[1].remaining_qty, 1.0, 5)

        # deliver lot2
        self.pick_out_prod_1.move_lines[0].move_line_ids[0].lot_id = self.prod_1_lot3
        self.pick_out_prod_1.move_lines[0].move_line_ids[0].qty_done = 1.0
        self.pick_out_prod_1.action_done()

        self.assertAlmostEqual(move.remaining_value, 12.0, 5)
        self.assertAlmostEqual(move.remaining_qty, 1.0, 5)
        self.assertAlmostEqual(move.move_line_ids[0].remaining_qty, 1.0, 5)
        self.assertAlmostEqual(move.move_line_ids[1].remaining_qty, 0.0, 5)

        entries = self.entry_obj.search(
            [('stock_move_id', 'in', self.pick_out_prod_1.move_lines.ids)])
        self.assertEqual(len(entries), 1)
        self.assertEqual(len(entries.line_ids), 2)

        entry_line = entries.line_ids.filtered(
            lambda x: x.account_id == self.account_inv)
        self.assertAlmostEqual(entry_line.credit, 12.0, 2)

    def test_inbound_multi_product(self):
        """Create inbound product moves, for a product with serial tracking, and
        for one without. Verify the stock.move.line.remaining_qty of both"""

        # receive lot2 and lot3 of product 1
        pick_in_prod_1 = self.picking_obj.create({
            'location_id': self.supplier_loc.id,
            'location_dest_id': self.stock_loc.id,
            'partner_id': self.partner_supplier.id,
            'picking_type_id': self.wh.in_type_id.id,
        })
        move1 = self.move_obj.create({
            'picking_id': pick_in_prod_1.id,
            'picking_type_id': self.wh.in_type_id.id,
            'name': self.prod_1.name,
            'product_id': self.prod_1.id,
            'product_uom_qty': 2.0,
            'product_uom': self.prod_1.uom_id.id,
            'location_id': self.supplier_loc.id,
            'location_dest_id': self.stock_loc.id,
            'warehouse_id': self.wh.id,
            'route_ids': [(6, 0, [self.wh.reception_route_id.id])],
            'state': 'draft',
            'quantity_done': 2.0,
            'price_unit': 12.0,
            'value': 24.0,
        })
        move1.move_line_ids.unlink()
        move1._action_confirm()
        move1._action_assign()
        pick_in_prod_1.move_lines[0].move_line_ids[0].write({
            'lot_id': self.prod_1_lot2.id,
            'qty_done': 1.0,
        })
        pick_in_prod_1.move_lines[0].move_line_ids[1].write({
            'lot_id': self.prod_1_lot3.id,
            'qty_done': 1.0,
        })

        # receive product 3
        move2 = self.move_obj.create({
            'picking_id': pick_in_prod_1.id,
            'picking_type_id': self.wh.in_type_id.id,
            'name': self.prod_3.name,
            'product_id': self.prod_3.id,
            'product_uom_qty': 2.0,
            'product_uom': self.prod_1.uom_id.id,
            'location_id': self.supplier_loc.id,
            'location_dest_id': self.stock_loc.id,
            'warehouse_id': self.wh.id,
            'route_ids': [(6, 0, [self.wh.reception_route_id.id])],
            'state': 'draft',
            'quantity_done': 2.0,
            'price_unit': 12.0,
            'value': 24.0,
        })
        move2._action_confirm()
        move2._action_assign()

        pick_in_prod_1.action_done()

        self.assertAlmostEqual(move1.remaining_value, 24.0, 5)
        self.assertAlmostEqual(move1.remaining_qty, 2.0, 5)
        self.assertAlmostEqual(move1.move_line_ids[0].remaining_qty, 1.0, 5)
        self.assertAlmostEqual(move1.move_line_ids[1].remaining_qty, 1.0, 5)

        self.assertAlmostEqual(move2.remaining_value, 24.0, 5)
        self.assertAlmostEqual(move2.remaining_qty, 2.0, 5)
        self.assertAlmostEqual(move2.move_line_ids.remaining_qty, 2.0, 5)
