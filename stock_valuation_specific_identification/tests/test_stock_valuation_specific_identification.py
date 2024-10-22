# Copyright 2024 Matt Taylor
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests.common import Form, TransactionCase
from odoo.exceptions import UserError


class TestStockValuationSpecIdent(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        product_category = cls.env["product.category"].create(
            {
                "name": "Test Category",
                "property_cost_method": "fifo",
                "property_valuation": "real_time",
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
                "categ_id": product_category.id,
                "tracking": "lot",
            }
        )
        cls.supplier_location = cls.env.ref("stock.stock_location_suppliers")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.picking_type_in = cls.env.ref("stock.picking_type_in")
        cls.picking_type_out = cls.env.ref("stock.picking_type_out")
        cls.company = cls.env.ref("base.main_company")
        cls.cost_account = cls.env.ref("l10n_generic_coa.1_cost_of_goods_sold")

    def create_picking(self, location, location_dest, picking_type):
        return self.env["stock.picking"].create(
            {
                "location_id": location.id,
                "location_dest_id": location_dest.id,
                "picking_type_id": picking_type.id,
            }
        )

    def create_stock_move(self, picking, product, qty, price=0.0):
        move = self.env["stock.move"].create(
            {
                "name": "Move",
                "product_id": product.id,
                "location_id": picking.location_id.id,
                "location_dest_id": picking.location_dest_id.id,
                "product_uom": product.uom_id.id,
                "product_uom_qty": qty,
                "picking_id": picking.id,
            }
        )
        if price:
            move.write({"price_unit": price})
        return move

    def create_stock_move_line(self, move, picking, qty, lot_name=False):
        move_line = self.env["stock.move.line"].create(
            {
                "move_id": move.id,
                "picking_id": picking.id,
                "product_id": move.product_id.id,
                "location_id": move.location_id.id,
                "location_dest_id": move.location_dest_id.id,
                "product_uom_id": move.product_uom.id,
                "qty_done": qty,
                "lot_name": lot_name,
            }
        )
        return move_line

# -----------------------------------------------------------------------------

    def test_revaluation_lot(self):
        """Verify revaluation affects lot price calculation"""
        receipt_picking_1 = self.create_picking(
            self.supplier_location, self.stock_location, self.picking_type_in
        )
        move = self.create_stock_move(
            receipt_picking_1,
            self.product,
            qty=5,
            price=1000,
        )
        self.create_stock_move_line(
            move,
            receipt_picking_1,
            qty=5,
            lot_name="11111",
        )
        receipt_picking_1.action_confirm()
        receipt_picking_1.action_assign()
        receipt_picking_1._action_done()

        receipt_picking_2 = self.create_picking(
            self.supplier_location, self.stock_location, self.picking_type_in
        )
        move = self.create_stock_move(
            receipt_picking_2,
            self.product,
            qty=5,
            price=2000,
        )
        self.create_stock_move_line(
            move,
            receipt_picking_2,
            qty=5,
            lot_name="22222",
        )
        receipt_picking_2.action_confirm()
        receipt_picking_2.action_assign()
        receipt_picking_2._action_done()

        lot2_id = self.env["stock.lot"].search(
            [("name", "=", "22222"), ("product_id", "=", self.product.id)]
        )

        wiz = (
            self.env["stock.valuation.layer.revaluation"]
            .sudo()
            .create(
                {
                    "company_id": self.company.id,
                    "product_id": self.product.id,
                    "lot_id": lot2_id.id,
                    "added_value": -500.0,
                    "account_id": self.cost_account.id,
                    "reason": "test serial revaluation",
                }
            )
        )
        wiz.action_validate_revaluation()

        delivery_picking = self.create_picking(
            self.stock_location, self.customer_location, self.picking_type_out
        )
        move = self.create_stock_move(
            delivery_picking,
            self.product,
            qty=1,
        )
        move_line = self.create_stock_move_line(
            move,
            delivery_picking,
            qty=1,
        )
        move_line.write({"lot_id": lot2_id})

        delivery_picking.action_confirm()
        delivery_picking.action_assign()
        delivery_picking._action_done()

        self.assertEqual(abs(move.stock_valuation_layer_ids.value), 1900)

    def test_multiple_valuation(self):
        """Verify that revaluation of layers with multiple lots is not allowed"""
        receipt_picking_1 = self.create_picking(
            self.supplier_location, self.stock_location, self.picking_type_in
        )
        move = self.create_stock_move(
            receipt_picking_1,
            self.product,
            qty=10,
            price=1000,
        )
        self.create_stock_move_line(
            move,
            receipt_picking_1,
            qty=5,
            lot_name="11111",
        )
        self.create_stock_move_line(
            move,
            receipt_picking_1,
            qty=5,
            lot_name="22222",
        )
        receipt_picking_1.action_confirm()
        receipt_picking_1.action_assign()
        receipt_picking_1._action_done()

        lot_id = self.env["stock.lot"].search(
            [("name", "=", "22222"), ("product_id", "=", self.product.id)]
        )

        wiz = (
            self.env["stock.valuation.layer.revaluation"]
            .sudo()
            .create(
                {
                    "company_id": self.company.id,
                    "product_id": self.product.id,
                    "lot_id": lot_id.id,
                    "added_value": -500.0,
                    "account_id": self.cost_account.id,
                    "reason": "test serial revaluation",
                }
            )
        )

        with self.assertRaises(UserError) as exc:
            wiz.action_validate_revaluation()
        self.assertEqual(
            exc.exception.args[0],
            "Can't revalue layers with multiple lots: 11111, 22222",
        )
