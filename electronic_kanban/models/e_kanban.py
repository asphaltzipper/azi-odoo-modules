# -*- coding: utf-8 -*-

from odoo import api, models, fields


class EKanbanBatch(models.Model):
    _name = "stock.e_kanban_batch"

    name = fields.Char(
        string='Name',
        copy=False,
        required=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('e.kanban.sequence'))

    batch_date = fields.Date(
        string='Batch Date',
        required=True,
        readonly=True,
        default=fields.Date.today(),
        index=True,
        copy=False,
        help="The date this batch was created.")

    line_ids = fields.One2many(
        comodel_name='stock.e_kanban_batch.line',
        inverse_name='batch_id')

    line_count = fields.Integer(
        compute='_compute_line_count',
        string='Bin Count',
        help='Number of Bins Scanned in this Batch')

    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('done', 'Done')],
        string='Status',
        default='draft',
        help="Draft: Draft\n"
             "Submitted:   Ordered but not received.\n"
             "Done: Received in to Stock.")

    @api.depends('line_ids')
    def _compute_line_count(self):
        for batch in self:
            batch.line_count = len(self.line_ids)


class EKanbanBatchLine(models.Model):
    _name = "stock.e_kanban_batch.line"

    batch_id = fields.Many2one(
        comodel_name='stock.e_kanban_batch',
        string='Batch')

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True)

    procurement_id = fields.Many2one(
        comodel_name='procurement.order',
        string='Procurement',
        readonly=True)

    rfq_qty = fields.Float(
        string='Unconfirmed Orders',
        compute='_compute_rfq_qty')

    incoming_qty = fields.Integer(
        string='Total to be Received',
        computed='_compute_incoming')

    product_manager = fields.Many2one(
        comodel_name='res.users',
        related='product_id.product_manager',
        store=True)

    default_supplier_id = fields.Many2one(
        string='supplier',
        comodel_name='product.supplierinfo',
        compute='_compute_default_supplier')

    latest_rcv_date = fields.Datetime(
        string='received date',
        compute='_compute_latest_rcv_date')

    @api.depends('product_id')
    def _compute_default_supplier(self):
        for line in self:
            line.default_supplier_id = line.product_id.seller_ids and line.product_id.seller_ids[0]

    @api.depends('product_id')
    def _compute_rfq_qty(self):
        loc_id = self.env['stock.warehouse'].search([], limit=1).wh_input_stock_loc_id.id
        stock_moves = self.env['stock.move']
        for line in self:
            domain = [
                ('product_id', '=', line.product_id.id),
                ('state', 'not in', ['done', 'cancel']),
                ('location_dest_id', '=', loc_id),
            ]
            moves = stock_moves.read_group(domain, ['product_id', 'product_uom_qty'], ['product_id'])
            line.rfq_qty = sum([x.product_uom_qty for x in moves])

    @api.depends('product_id')
    def _compute_latest_rcv_date(self):
        location_id = self.env['stock.warehouse'].search([], limit=1).wh_input_stock_loc_id.id
        stock_moves = self.env['stock.move']
        for line in self:
            domain = [
                ('product_id', '=', line.product_id.id),
                ('state', '=', 'done'),
                ('location_dest_id', '=', location_id),
            ]
            moves = stock_moves.search(domain, order='date desc', limit=1)
            line.incoming_qty = sum([x.product_uom_qty for x in moves])

    @api.depends('product_id')
    def _compute_incoming(self):
        location_id = self.env['stock.warehouse'].search([], limit=1).wh_input_stock_loc_id.id
        stock_moves = self.env['stock.move']
        for line in self:
            domain = [
                ('product_id', '=', line.product_id.id),
                ('state', 'not in', ['done', 'cancel']),
                ('move_dest_id', '=', location_id),
            ]
            moves = stock_moves.read_group(domain, ['product_id', 'product_uom_qty'], ['product_id'])
            line.incoming_qty = sum([x.product_uom_qty for x in moves])

    @api.multi
    def action_convert_to_procurements(self):
        warehouse = self.env['stock.warehouse'].search([], limit=1)
        # TODO: add option to choose day of week for procurement with weekly buckets
        procurement_order = self.env['procurement.order']
        for line in self:
            proc_name = "Hello World"
            self.procurement_id = procurement_order.create(
                {
                    'name': proc_name,
                    'product_id': line.product_id.id,
                    'product_qty': line.product_id.default_proc_qty,
                    'product_uom': line.product_id.uom_id.id,
                    'warehouse_id': warehouse.id,
                    # 'location_id': warehouse.lot_stock_id.id,
                }
            )
