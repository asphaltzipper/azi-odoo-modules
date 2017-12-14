# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError


class EKanbanBatch(models.Model):
    _name = "stock.e_kanban_batch"
    _inherit = ['barcodes.barcode_events_mixin']

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

    _barcode_scanned = fields.Char(
        string="Barcode Scanned",
        help="Value of the last barcode scanned.",
        store=False)

    @api.depends('line_ids')
    def _compute_line_count(self):
        for batch in self:
            batch.line_count = len(self.line_ids.ids)

    @api.model
    def ekb_barcode(self, barcode, ekb_id):
        batch = self.env['stock.e_kanban_batch'].search([('id', '=', ekb_id)])
        if not batch:
            raise UserError(_('No Batch Found/ so Save!'))
        product_id = self.env['product.product'].search([('barcode', '=', barcode)])
        line_values = {
            'product_id': product_id.id,
            'batch_id': batch.id,
        }
        batch.update({'line_ids': [(0, 0, line_values)]})


class EKanbanBatchLine(models.Model):
    _name = "stock.e_kanban_batch.line"

    batch_id = fields.Many2one(
        comodel_name='stock.e_kanban_batch',
        readonly=True,
        string='Batch')

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True)

    default_proc_qty = fields.Float(
        string='Bin Qty',
        related='product_id.default_proc_qty',
        readonly=True,
        store=True)

    e_kanban = fields.Boolean(
        string='Is Kanban',
        related='product_id.e_kanban',
        readonly=True,
        store=True)

    procurement_id = fields.Many2one(
        comodel_name='procurement.order',
        string='Procurement',
        readonly=True)

    rfq_qty = fields.Float(
        string='Open RFQs',
        readonly=True,
        required=True)

    incoming_qty = fields.Float(
        string='Pending Receipts',
        readonly=True,
        required=True)

    product_manager = fields.Many2one(
        comodel_name='res.users',
        readonly=True,
        related='product_id.product_manager',
        store=True)

    default_supplier_id = fields.Many2one(
        string='Supplier',
        comodel_name='res.partner',
        compute='_compute_default_supplier',
        store=True)

    latest_rcv_date = fields.Datetime(
        # compute='_get_static_rcv_date',
        readonly=True,
        string='Latest Receipt')

    def _get_static_incoming(self, product_id):
        loc_id = self.env['stock.warehouse'].search([], limit=1).lot_stock_id.id
        stock_moves = self.env['stock.move']
        domain = [
            ('product_id', '=', product_id),
            ('state', 'not in', ['done', 'cancel']),
            ('location_dest_id', '=', loc_id),
        ]
        moves = stock_moves.read_group(domain, ['product_id', 'product_uom_qty'], ['product_id'])
        return sum([x['product_uom_qty'] for x in moves])

    def _get_static_rfq_qty(self, product_id):
        rfq_lines = self.env['purchase.order.line']
        domain = [
            ('product_id', '=', product_id),
            ('state', 'not in', ['done', 'purchase', 'cancel']),
        ]
        rfqs = rfq_lines.search(domain)
        qty_sum = 0
        for rfq in rfqs:
            qty_sum += rfq.product_qty
        return qty_sum

    def _get_static_rcv_date(self, product_id):
        loc_id = self.env['stock.warehouse'].search([], limit=1).wh_input_stock_loc_id.id
        stock_moves = self.env['stock.move']
        domain = [
            ('product_id', '=', product_id),
            ('state', '=', 'done'),
            ('location_dest_id', '=', loc_id),
        ]
        move = stock_moves.search(domain, order='date desc', limit=1)
        return move.date

    @api.model
    def create(self, vals):
        vals['rfq_qty'] = self._get_static_rfq_qty(vals['product_id'])
        vals['incoming_qty'] = self._get_static_incoming(vals['product_id'])
        vals['latest_rcv_date'] = self._get_static_rcv_date(vals['product_id'])
        return super(EKanbanBatchLine, self).create(vals)

    @api.depends('product_id')
    def _compute_default_supplier(self):
        for line in self:
            line.default_supplier_id = line.product_id.seller_ids and line.product_id.seller_ids[0].name or False

    @api.depends('product_id')
    def _compute_rfq_qty(self):
        rfq_lines = self.env['purchase.order.line']
        for line in self:
            domain = [
                ('product_id', '=', line.product_id.id),
                ('state', 'not in', ['done', 'purchase', 'cancel']),
            ]
            rfqs = rfq_lines.search(domain)
            qty_sum = 0
            for rfq in rfqs:
                qty_sum += rfq.product_qty
            line.rfq_qty = qty_sum

    @api.depends('product_id')
    def _compute_latest_rcv_date(self):
        loc_id = self.env['stock.warehouse'].search([], limit=1).wh_input_stock_loc_id.id
        stock_moves = self.env['stock.move']
        for line in self:
            domain = [
                ('product_id', '=', line.product_id.id),
                ('state', '=', 'done'),
                ('location_dest_id', '=', loc_id),
            ]
            move = stock_moves.search(domain, order='date desc', limit=1)
            line.rcv_date = move.date

    @api.depends('product_id')
    def _compute_incoming(self):
        loc_id = self.env['stock.warehouse'].search([], limit=1).wh_input_stock_loc_id.id
        stock_moves = self.env['stock.move']
        for line in self:
            domain = [
                ('product_id', '=', line.product_id.id),
                ('state', 'not in', ['done', 'cancel']),
                ('move_dest_id', '=', loc_id),
            ]
            moves = stock_moves.read_group(domain, ['product_id', 'product_uom_qty'], ['product_id'])
            line.incoming_qty = sum([x['product_uom_qty'] for x in moves])

    @api.multi
    def action_convert_to_procurements(self):
        warehouse = self.env['stock.warehouse'].search([], limit=1)
        procurement_order = self.env['procurement.order']
        for line in self:
            if line.procurement_id:
                raise UserError("Trying to Create Duplicate Order for %s" % line.product_id.display_name)
            proc_name = "%s/%s" % (line.batch_id.name, line.product_id.default_code)
            line.procurement_id = procurement_order.create(
                {
                    'name': proc_name,
                    'product_id': line.product_id.id,
                    'product_qty': line.product_id.default_proc_qty,
                    'product_uom': line.product_id.uom_id.id,
                    'warehouse_id': warehouse.id,
                    'location_id': warehouse.lot_stock_id.id,
                }
            )
