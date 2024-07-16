# Copyright 2020 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestStockFifoLotCostingCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.category_obj = cls.env['product.category']
        cls.product_obj = cls.env['product.product']
        cls.template_obj = cls.env['product.template']
        cls.inventory_obj = cls.env['stock.inventory']
        cls.lot_obj = cls.env['stock.lot']
        cls.location_obj = cls.env['stock.location']
        cls.account_obj = cls.env['account.account']
        cls.entry_obj = cls.env['account.move']
        cls.journal_obj = cls.env['account.journal']
        cls.picking_obj = cls.env['stock.picking']
        cls.move_obj = cls.env['stock.move']

        cls.uom_unit = cls.env.ref('uom.product_uom_unit')
        cls.company = cls.env.ref('base.main_company')

        # Account types
        expense_type = 'other_account_type_expenses'
        liability_type = 'other_account_type_current_liabilities'
        asset_type = 'other_account_type_current_assets'

        # Create account for Goods Received Not Invoiced
        cls.account_grni = cls.account_obj.create({
            'name': 'Goods Received Not Invoiced',
            'code': 'grni',
            'account_type': liability_type,
            'company_id': cls.company.id,
        })
        # Create account for Cost of Goods Sold
        cls.account_cogs = cls.account_obj.create({
            'name': 'Cost of Goods Sold',
            'code': 'cogs',
            'account_type': expense_type,
            'company_id': cls.company.id,
        })
        # Create account for Inventory
        cls.account_inv = cls.account_obj.create({
            'name': 'Inventory',
            'code': 'inv',
            'account_type': asset_type,
            'company_id': cls.company.id,
        })
        # get stock journal
        cls.stock_journal = cls.journal_obj.search(
            [('name', '=', 'Stock Journal')])

        # create FIFO product category
        cls.category_1 = cls.category_obj.create({
            'name': 'test_product_ctg',
            'property_stock_valuation_account_id': cls.account_inv.id,
            'property_stock_account_input_categ_id': cls.account_grni.id,
            'property_stock_account_output_categ_id': cls.account_cogs.id,
            'property_stock_journal': cls.stock_journal.id,
            'property_cost_method': 'fifo',
            'property_valuation': 'real_time',
        })

        # create products
        cls.template_1 = cls.template_obj.create({
            'name': 'Test Product 1',
            'type': 'product',
            'categ_id': cls.category_1.id,
            'tracking': 'serial',
        })
        cls.prod_1 = cls.product_obj.create({
            'product_tmpl_id': cls.template_1.id,
        })
        cls.template_2 = cls.template_obj.create({
            'name': 'Test Product 2',
            'type': 'product',
            'categ_id': cls.category_1.id,
            'tracking': 'lot',
        })
        cls.prod_2 = cls.product_obj.create({
            'product_tmpl_id': cls.template_2.id,
        })
        cls.template_3 = cls.template_obj.create({
            'name': 'Test Product 3',
            'type': 'product',
            'categ_id': cls.category_1.id,
            'tracking': 'none',
        })
        cls.prod_3 = cls.product_obj.create({
            'product_tmpl_id': cls.template_3.id,
        })

        cls.prod_1_lot1 = cls.lot_obj.create({
            'name': 'TSTPROD1LOT01',
            'product_id': cls.prod_1.id,
        })
        cls.prod_1_lot2 = cls.lot_obj.create({
            'name': 'TSTPROD1LOT02',
            'product_id': cls.prod_1.id,
        })
        cls.prod_1_lot3 = cls.lot_obj.create({
            'name': 'TSTPROD1LOT03',
            'product_id': cls.prod_1.id,
        })
        cls.prod_2_lot1 = cls.lot_obj.create({
            'name': 'TSTPROD2LOT01',
            'product_id': cls.prod_2.id,
        })
        cls.prod_2_lot2 = cls.lot_obj.create({
            'name': 'TSTPROD2LOT02',
            'product_id': cls.prod_2.id,
        })
        cls.prod_2_lot3 = cls.lot_obj.create({
            'name': 'TSTPROD2LOT03',
            'product_id': cls.prod_2.id,
        })

        # get locations

        cls.wh = cls.env.ref('stock.warehouse0')
        loc = cls.location_obj.search([('name', '=', 'WH')])
        cls.stock_loc = cls.location_obj.search([('location_id', '=', loc.id)])
        cls.inventory_loc = cls.env.ref('stock.location_inventory')
        cls.supplier_loc = cls.env.ref('stock.stock_location_suppliers')
        cls.customer_loc = cls.env.ref('stock.stock_location_customers')

        # create supplier
        cls.partner_supplier = cls.env['res.partner'].create({
            'name': 'Mrs. OCA',
            'property_stock_supplier': cls.supplier_loc.id,
            'property_stock_customer': cls.customer_loc.id,
        })

        # create inbound picking for prod_1
        cls.pick_in_prod_1 = cls.picking_obj.create({
            'location_id': cls.supplier_loc.id,
            'location_dest_id': cls.stock_loc.id,
            'partner_id': cls.partner_supplier.id,
            'picking_type_id': cls.wh.in_type_id.id,
            'move_lines': [
                (0, 0, {
                    'name': cls.prod_1.name,
                    'product_id': cls.prod_1.id,
                    'product_uom_qty': 1.0,
                    'product_uom': cls.prod_1.uom_id.id,
                    'quantity_done': 1.0,
                }),
            ],
        })
        cls.pick_in_prod_1.action_confirm()
        cls.pick_in_prod_1.action_assign()

        # create customer
        cls.partner_customer = cls.env['res.partner'].create({
            'name': 'Mr. Odoo',
            'property_stock_supplier': cls.supplier_loc.id,
            'property_stock_customer': cls.customer_loc.id,
        })

        # create outbound picking for prod_1
        cls.pick_out_prod_1 = cls.picking_obj.create({
            'location_id': cls.stock_loc.id,
            'location_dest_id': cls.customer_loc.id,
            'partner_id': cls.partner_customer.id,
            'picking_type_id': cls.wh.out_type_id.id,
            'move_lines': [
                (0, 0, {
                    'name': cls.prod_1.name,
                    'product_id': cls.prod_1.id,
                    'product_uom_qty': 1.0,
                    'product_uom': cls.prod_1.uom_id.id,
                    'quantity_done': 1.0,
                }),
            ],
        })
        cls.pick_out_prod_1.action_confirm()
        cls.pick_out_prod_1.action_assign()





        # cls.wh1 = cls.env['stock.warehouse'].create({
        #     'name': 'TEST WH1',
        #     'code': 'TST1',
        # })
        #
        # # Locations (WH1 locations are created automatically)
        # location_obj = cls.env['stock.location']
        # cls.supplier_loc = location_obj.create({
        #     'name': 'Test supplier location',
        #     'usage': 'supplier',
        # })
        # cls.customer_loc = location_obj.create({
        #     'name': 'Test customer location',
        #     'usage': 'customer',
        # })
        # # Create child locations
        # cls.location_child_1 = location_obj.create({
        #     'location_id': cls.wh1.lot_stock_id.id,
        #     'name': 'Location child 1',
        # })
        #
        # # Create partners
        # cls.partner_customer = cls.env['res.partner'].create({
        #     'name': 'Mr. Odoo',
        #     'property_stock_supplier': cls.supplier_loc.id,
        #     'property_stock_customer': cls.customer_loc.id,
        # })
        # cls.partner_supplier = cls.env['res.partner'].create({
        #     'name': 'Mrs. OCA',
        #     'property_stock_supplier': cls.supplier_loc.id,
        #     'property_stock_customer': cls.customer_loc.id,
        # })
        # # Create deliveries and receipts orders to have a history
        # # First, some incoming pickings
        # cls.picking_obj = cls.env['stock.picking']
        # cls.picking_supplier_1 = cls.picking_obj.create({
        #     'location_id': cls.supplier_loc.id,
        #     'location_dest_id': cls.wh1.lot_stock_id.id,
        #     'partner_id': cls.partner_supplier.id,
        #     'picking_type_id': cls.wh1.in_type_id.id,
        #     'move_lines': [
        #         (0, 0, {
        #             'name': cls.prod_1.name,
        #             'product_id': cls.prod_1.id,
        #             'product_uom_qty': 10.0,
        #             'product_uom': cls.prod_1.uom_id.id,
        #             'quantity_done': 10.0,
        #         }),
        #         (0, 0, {
        #             'name': cls.prod_2.name,
        #             'product_id': cls.prod_2.id,
        #             'product_uom_qty': 20.0,
        #             'product_uom': cls.prod_2.uom_id.id,
        #             'quantity_done': 20.0,
        #         }),
        #         (0, 0, {
        #             'name': cls.prod_3.name,
        #             'product_id': cls.prod_3.id,
        #             'product_uom_qty': 30.0,
        #             'product_uom': cls.prod_3.uom_id.id,
        #         }),
        #         (0, 0, {
        #             'name': cls.prod_1.name,
        #             'product_id': cls.prod_1.id,
        #             'product_uom_qty': 50.0,
        #             'product_uom': cls.prod_1.uom_id.id,
        #             'location_dest_id': cls.location_child_1,
        #         }),
        #         (0, 0, {
        #             'name': cls.prod_1.name,
        #             'product_id': cls.prod_1.id,
        #             'product_uom_qty': 75.0,
        #             'product_uom': cls.prod_1.uom_id.id,
        #             'location_dest_id': cls.location_child_2,
        #         }),
        #     ],
        # })
        # move3 = cls.picking_supplier_1.move_lines.filtered(
        #     lambda x: x.product_id == cls.prod_3)
        # move3.write({
        #     'move_line_ids': [
        #         (0, 0, {
        #             'picking_id': cls.picking_supplier_1.id,
        #             'lot_id': cls.prod_3_lot1.id,
        #             'product_id': cls.prod_3.id,
        #             'product_uom_id': cls.prod_3.uom_id.id,
        #             'location_id': cls.supplier_loc.id,
        #             'location_dest_id': cls.wh1.lot_stock_id.id,
        #             'qty_done': 20,
        #         }),
        #         (0, 0, {
        #             'picking_id': cls.picking_supplier_1.id,
        #             'product_id': cls.prod_3.id,
        #             'product_uom_id': cls.prod_3.uom_id.id,
        #             'lot_id': cls.prod_3_lot2.id,
        #             'location_id': cls.supplier_loc.id,
        #             'location_dest_id': cls.wh1.lot_stock_id.id,
        #             'qty_done': 10,
        #         }),
        #     ],
        # })
        # move3.qty_done = 30
        # cls.picking_supplier_1.action_confirm()
        # cls.picking_supplier_1.action_assign()
        # cls.picking_supplier_1.action_done()
        # cls.picking_supplier_2 = cls.picking_supplier_1.copy({
        #     'move_lines': [
        #         (0, 0, {
        #             'name': cls.prod_1.name,
        #             'product_id': cls.prod_1.id,
        #             'product_uom_qty': 90.0,
        #             'product_uom': cls.prod_1.uom_id.id,
        #             'quantity_done': 90.0,
        #         }),
        #         (0, 0, {
        #             'name': cls.prod_2.name,
        #             'product_id': cls.prod_2.id,
        #             'product_uom_qty': 80.0,
        #             'product_uom': cls.prod_2.uom_id.id,
        #             'quantity_done': 90.0,
        #         }),
        #         (0, 0, {
        #             'name': cls.prod_3.name,
        #             'product_id': cls.prod_3.id,
        #             'product_uom_qty': 70.0,
        #             'product_uom': cls.prod_3.uom_id.id,
        #         })],
        # })
        # move3 = cls.picking_supplier_2.move_lines.filtered(
        #     lambda x: x.product_id == cls.prod_3)
        # move3.write({
        #     'move_line_ids': [
        #         (0, 0, {
        #             'picking_id': cls.picking_supplier_2.id,
        #             'lot_id': cls.prod_3_lot1.id,
        #             'product_id': cls.prod_3.id,
        #             'product_uom_id': cls.prod_3.uom_id.id,
        #             'location_id': cls.supplier_loc.id,
        #             'location_dest_id': cls.wh1.lot_stock_id.id,
        #             'qty_done': 70,
        #         }),
        #     ],
        # })
        # move3.qty_done = 30
        # cls.picking_supplier_2.action_confirm()
        # cls.picking_supplier_2.action_assign()
        # cls.picking_supplier_2.action_done()
        # # We'll have 100 units of each product
        # # No we deliver some products
        # cls.picking_customer_1 = cls.picking_obj.create({
        #     'location_id': cls.wh1.lot_stock_id.id,
        #     'location_dest_id': cls.customer_loc.id,
        #     'partner_id': cls.partner_customer.id,
        #     'picking_type_id': cls.wh1.out_type_id.id,
        #     'move_lines': [
        #         (0, 0, {
        #             'name': cls.prod_1.name,
        #             'product_id': cls.prod_1.id,
        #             'product_uom_qty': 10.0,
        #             'product_uom': cls.prod_1.uom_id.id,
        #             'quantity_done': 10.0,
        #         }),
        #         (0, 0, {
        #             'name': cls.prod_2.name,
        #             'product_id': cls.prod_2.id,
        #             'product_uom_qty': 20.0,
        #             'product_uom': cls.prod_2.uom_id.id,
        #             'quantity_done': 20.0,
        #         })],
        # })
        # cls.picking_customer_1.action_confirm()
        # cls.picking_customer_1.action_assign()
        # cls.picking_customer_1.action_done()
        # cls.picking_customer_2 = cls.picking_customer_1.copy({
        #     'move_lines': [
        #         (0, 0, {
        #             'name': cls.prod_1.name,
        #             'product_id': cls.prod_1.id,
        #             'product_uom_qty': 10.0,
        #             'product_uom': cls.prod_1.uom_id.id,
        #             'quantity_done': 10.0,
        #         }),
        #         (0, 0, {
        #             'name': cls.prod_2.name,
        #             'product_id': cls.prod_2.id,
        #             'product_uom_qty': 10.0,
        #             'product_uom': cls.prod_2.uom_id.id,
        #             'quantity_done': 10.0,
        #         })],
        # })
        # cls.picking_customer_2.action_confirm()
        # cls.picking_customer_2.action_assign()
        # cls.picking_customer_2.action_done()
        # # Stock in wh1.lot_stock_id
        # # prod_1: 80.0 / prod_2: 70.0 / prod_3: 100.0
        # cls.return_request_obj = cls.env['stock.return.request']
        # # Return from customer
        # cls.return_request_customer = cls.return_request_obj.create({
        #     'partner_id': cls.partner_customer.id,
        #     'return_type': 'customer',
        #     'return_to_location': cls.wh1.lot_stock_id.id,
        #     'return_from_location': cls.wh1.lot_stock_id.id,
        #     'return_order': 'date desc, id desc',  # Newer first
        # })
        # cls.return_request_customer.onchange_locations()
        # cls.return_request_supplier = cls.return_request_customer.copy({
        #     'partner_id': cls.partner_supplier.id,
        #     'return_to_location': cls.wh1.lot_stock_id.id,
        #     'return_from_location': cls.wh1.lot_stock_id.id,
        #     'return_type': 'supplier',
        #     'return_order': 'date asc, id desc',  # Older first
        # })
        # cls.return_request_supplier.onchange_locations()
