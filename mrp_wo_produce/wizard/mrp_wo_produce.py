# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round


class MrpWoProduceWork(models.TransientModel):
    _name = "mrp.wo.produce.work"
    _description = 'Workorder Labor Details'

    produce_id = fields.Many2one(
        comodel_name='mrp.wo.produce',
        required=True)

    production_id = fields.Many2one(
        comodel_name='mrp.production',
        related='produce_id.production_id')

    workorder_id = fields.Many2one(
        comodel_name='mrp.workorder',
        string="Work Order",
        required=True)

    user_id = fields.Many2one(
        comodel_name='res.users',
        string="User",)

    user_ids = fields.Many2many(
        'res.users',
        compute='_compute_user_ids')

    labor_date = fields.Datetime(
        string="Date")

    labor_time = fields.Float(
        string='Hours')

    hours_expected = fields.Float(
        string='Standard',
        compute='_compute_hours_expected')

    @api.multi
    @api.depends('workorder_id')
    def _compute_hours_expected(self):
        for rec in self:
            rec.hours_expected = rec.produce_id.product_qty * rec.workorder_id.duration_expected / 60

    @api.multi
    @api.depends('workorder_id')
    def _compute_user_ids(self):
        for record in self:
            users = self.env['resource.resource'].search([('active', '=', True), ('resource_type', '=', 'user'),
                                                          ('user_id', '!=', False)]).mapped('user_id').ids
            user_ids = self.env['res.users'].search([('active', '=', True)]).ids
            record.user_ids = [(6, _, list(set(users + user_ids)))]


class MrpWoProduce(models.TransientModel):
    """
    Show a button to execute this wizard whenever there are work orders
    associated with this MO.  i.e. The button should only show after the user
    has clicked the Plan button.

    Return an error if the user attempts to start this wizard before providing
    all required serial numbers. Serial numbers should be specified on the MO,
    rather than on the individual work orders.

    This wizard is a copy of the mrp.product.produce wizard.  Extending that
    wizard to handle routings/workorders would make it too complex.
    """
    _name = "mrp.wo.produce"
    _description = 'Produce MO with Workorders'

    serial = fields.Boolean('Requires Serial')
    production_id = fields.Many2one('mrp.production', 'Production')
    work_ids = fields.One2many('mrp.wo.produce.work', 'produce_id', "Work Order Labor")
    product_id = fields.Many2one('product.product', 'Product')
    product_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True)
    product_uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    lot_id = fields.Many2one('stock.production.lot', string='Lot/Serial Number')
    produce_line_ids = fields.One2many('mrp.wo.produce.line', 'product_produce_id', string='Product to Track')
    product_tracking = fields.Selection(related="product_id.tracking", readonly=True)

    @api.model
    def default_get(self, fields):
        res = super(MrpWoProduce, self).default_get(fields)
        if res.get('production_id'):
            production = self.env['mrp.production'].browse(res['production_id'])
        elif self._context and self._context.get('default_production_id'):
            production = self.env['mrp.production'].browse(self._context['default_production_id'])
        elif self._context and self._context.get('active_model', '') == 'mrp.production' and self._context.get('active_id'):
            production = self.env['mrp.production'].browse(self._context['active_id'])
        else:
            raise UserError("Change Quantity Wizard called without reference to a Manufacturing Order")
        if production:
            serial_finished = (production.product_id.tracking == 'serial')
            todo_uom = production.product_uom_id.id
            if serial_finished:
                todo_quantity = 1.0
                if production.product_uom_id.uom_type != 'reference':
                    todo_uom = self.env['uom.uom'].search(
                        [('category_id', '=', production.product_uom_id.category_id.id),
                         ('uom_type', '=', 'reference')]).id
            else:
                main_product_moves = production.move_finished_ids.filtered(
                    lambda x: x.product_id.id == production.product_id.id)
                todo_quantity = production.product_qty - sum(main_product_moves.mapped('quantity_done'))
                todo_quantity = todo_quantity if (todo_quantity > 0) else 0
            if 'production_id' in fields:
                res['production_id'] = production.id
            if 'product_id' in fields:
                res['product_id'] = production.product_id.id
            if 'product_uom_id' in fields:
                res['product_uom_id'] = todo_uom
            if 'serial' in fields:
                res['serial'] = bool(serial_finished)
            if 'product_qty' in fields:
                res['product_qty'] = todo_quantity
        return res

    @api.onchange('product_qty')
    def _onchange_product_qty(self):
        lines = []
        qty_todo = self.product_uom_id._compute_quantity(self.product_qty, self.production_id.product_uom_id,
                                                         round=False)
        for move in self.production_id.move_raw_ids.filtered(
                lambda m: m.state not in ('done', 'cancel') and m.bom_line_id):
            qty_to_consume = float_round(qty_todo * move.unit_factor, precision_rounding=move.product_uom.rounding)
            for move_line in move.move_line_ids:
                if float_compare(qty_to_consume, 0.0, precision_rounding=move.product_uom.rounding) <= 0:
                    break
                if move_line.lot_produced_id or float_compare(move_line.product_uom_qty, move_line.qty_done,
                                                              precision_rounding=move.product_uom.rounding) <= 0:
                    continue
                to_consume_in_line = min(qty_to_consume, move_line.product_uom_qty)
                lines.append({
                    'move_id': move.id,
                    'qty_to_consume': to_consume_in_line,
                    'qty_done': to_consume_in_line,
                    'lot_id': move_line.lot_id.id,
                    'product_uom_id': move.product_uom.id,
                    'product_id': move.product_id.id,
                    'qty_reserved': min(to_consume_in_line, move_line.product_uom_qty),
                })
                qty_to_consume -= to_consume_in_line
            if float_compare(qty_to_consume, 0.0, precision_rounding=move.product_uom.rounding) > 0:
                if move.product_id.tracking == 'serial':
                    while float_compare(qty_to_consume, 0.0, precision_rounding=move.product_uom.rounding) > 0:
                        lines.append({
                            'move_id': move.id,
                            'qty_to_consume': 1,
                            'qty_done': 1,
                            'product_uom_id': move.product_uom.id,
                            'product_id': move.product_id.id,
                        })
                        qty_to_consume -= 1
                else:
                    lines.append({
                        'move_id': move.id,
                        'qty_to_consume': qty_to_consume,
                        'qty_done': qty_to_consume,
                        'product_uom_id': move.product_uom.id,
                        'product_id': move.product_id.id,
                    })

        self.produce_line_ids = [(0, 0, x) for x in lines]

    @api.multi
    def load_work(self):
        for wo in self.production_id.workorder_ids:
            self.work_ids.create({
                'produce_id': self.id,
                'workorder_id': wo.id,
            })
        action = self.env.ref('mrp_wo_produce.act_mrp_wo_produce_wizard').read()[0]
        action['res_id'] = self.id
        return action

    @api.multi
    def do_produce(self):
        # apply work time to work orders
        self.update_work_time()

        # if work time was successfully applied to the work orders:
        # complete the work orders
        self.complete_workorders()

        # Nothing to do for lots since values are created using default data (stock.move.lots)
        quantity = self.product_qty
        if float_compare(quantity, 0, precision_rounding=self.product_uom_id.rounding) <= 0:
            raise UserError(
                _("The production order for '%s' has no quantity specified.") % self.product_id.display_name)
        for move in self.production_id.move_finished_ids:
            if move.product_id.tracking == 'none' and move.state not in ('done', 'cancel'):
                rounding = move.product_uom.rounding
                if move.product_id.id == self.production_id.product_id.id:
                    move.quantity_done += float_round(quantity, precision_rounding=rounding)
                elif move.unit_factor:
                    # byproducts handling
                    move.quantity_done += float_round(quantity * move.unit_factor, precision_rounding=rounding)
        self.check_finished_move_lots()
        if self.production_id.state == 'confirmed':
            self.production_id.write({
                'state': 'progress',
                'date_start': datetime.now(),
            })
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def check_finished_move_lots(self):
        produce_move = self.production_id.move_finished_ids.filtered(
            lambda x: x.product_id == self.product_id and x.state not in ('done', 'cancel'))
        if produce_move and produce_move.product_id.tracking != 'none':
            if not self.lot_id:
                raise UserError(_('You need to provide a lot for the finished product.'))
            existing_move_line = produce_move.move_line_ids.filtered(lambda x: x.lot_id == self.lot_id)
            if existing_move_line:
                if self.product_id.tracking == 'serial':
                    raise UserError(_('You cannot produce the same serial number twice.'))
                produced_qty = self.product_uom_id._compute_quantity(self.product_qty,
                                                                     existing_move_line.product_uom_id)
                existing_move_line.product_uom_qty += produced_qty
                existing_move_line.qty_done += produced_qty
            else:
                vals = {
                    'move_id': produce_move.id,
                    'product_id': produce_move.product_id.id,
                    'production_id': self.production_id.id,
                    'product_uom_qty': self.product_qty,
                    'product_uom_id': self.product_uom_id.id,
                    'qty_done': self.product_qty,
                    'lot_id': self.lot_id.id,
                    'location_id': produce_move.location_id.id,
                    'location_dest_id': produce_move.location_dest_id.id,
                }
                self.env['stock.move.line'].create(vals)

        for pl in self.produce_line_ids:
            if pl.qty_done:
                if pl.product_id.tracking != 'none' and not pl.lot_id:
                    raise UserError(_('Please enter a lot or serial number for %s !' % pl.product_id.display_name))
                if not pl.move_id:
                    # Find move_id that would match
                    move_id = self.production_id.move_raw_ids.filtered(
                        lambda m: m.product_id == pl.product_id and m.state not in ('done', 'cancel'))
                    if move_id:
                        pl.move_id = move_id
                    else:
                        # create a move and put it in there
                        order = self.production_id
                        pl.move_id = self.env['stock.move'].create({
                            'name': order.name,
                            'product_id': pl.product_id.id,
                            'product_uom': pl.product_uom_id.id,
                            'location_id': order.location_src_id.id,
                            'location_dest_id': self.product_id.property_stock_production.id,
                            'raw_material_production_id': order.id,
                            'group_id': order.procurement_group_id.id,
                            'origin': order.name,
                            'state': 'confirmed'})
                pl.move_id._generate_consumed_move_line(pl.qty_done, self.lot_id, lot=pl.lot_id)
        return True

    @api.multi
    def update_work_time(self):
        """this method has been adapted from mrp.workorder methods button_start() and end_previous()"""

        # verify all work orders have time reported
        reported_workorders = self.work_ids.mapped('workorder_id')
        unreported_workorder_ids = self.production_id.workorder_ids\
            .filtered(lambda x: x.id not in reported_workorders.ids and x.duration_expected > 0.0).ids
        work_summary = self.work_ids.read_group(
            domain=[('produce_id', '=', self.id)],
            fields=['workorder_id', 'labor_time'],
            groupby=['workorder_id'])
        tolerance = 0.0001
        zero_work_ids = [
            x['workorder_id'][0] for x in work_summary if x['labor_time'] < tolerance
        ]
        error_domain = ['|', ('id', 'in', unreported_workorder_ids),
                        '&', ('duration_expected', '>', tolerance), ('id', 'in', zero_work_ids)]
        unreported_workorders = self.env['mrp.workorder'].search(error_domain)
        if len(unreported_workorders):
            raise UserError(
                "You must specify labor time for work orders: %s" %
                ", ".join(unreported_workorders.mapped('name')))

        # verify required fields
        if self.work_ids.filtered(lambda x: not x.user_id or not x.labor_date):
            raise UserError("Labor date and user are required for all work orders.")

        # we first delete any previously recorded work order time
        self.production_id.workorder_ids.mapped('time_ids').unlink()

        # get productivity types
        productive_id = self.env['mrp.workcenter.productivity.loss'].search([('loss_type', '=', 'productive')], limit=1)
        if not len(productive_id):
            raise UserError(_("You need to define at least one productivity loss in the category 'Productivity'. Create one from the Manufacturing app, menu: Configuration / Productivity Losses."))
        performance_id = self.env['mrp.workcenter.productivity.loss'].search([('loss_type', '=', 'performance')], limit=1)
        if not len(performance_id):
            raise UserError(_("You need to define at least one productivity loss in the category 'Performance'. Create one from the Manufacturing app, menu: Configuration / Productivity Losses."))

        # proceed with applying user-specified work order time
        timeline = self.env['mrp.workcenter.productivity']
        for work in self.work_ids:
            time_minutes = work.labor_time * 60

            template = {
                'workorder_id': work.workorder_id.id,
                'workcenter_id': work.workorder_id.workcenter_id.id,
                'user_id': work.user_id.id,
                'description': _('Time Tracking: ') + work.user_id.name,
                'date_start': work.labor_date,
                'date_end': fields.Datetime.from_string(work.labor_date) + relativedelta(minutes=time_minutes),
            }
            if time_minutes + work.workorder_id.duration <= work.workorder_id.duration_expected:
                # previous time plus time to be added is less than the expected duration
                # all time to be added is considered productive
                tmp = template.copy()
                tmp['loss_id'] = productive_id.id
                timeline.create(tmp)
            elif work.workorder_id.duration >= work.workorder_id.duration_expected:
                # the wo is already over the expected duration
                # all time to be added is categorized as performance loss
                tmp = template.copy()
                tmp['loss_id'] = performance_id.id
                timeline.create(tmp)
            else:
                # time to be added will put the wo over it's expected duration
                # some of the time is productive, the remaining is categorized as performance loss
                productive_time = work.workorder_id.duration_expected - work.workorder_id.duration
                performance_time = time_minutes - productive_time
                productive_date_end = fields.Datetime.from_string(work.labor_date) + relativedelta(minutes=productive_time)
                performance_date_end = productive_date_end + relativedelta(minutes=performance_time)
                tmp = template.copy()

                tmp['loss_id'] = productive_id.id
                tmp['date_end'] = productive_date_end
                timeline.create(tmp)

                tmp['loss_id'] = performance_id.id
                tmp['date_start'] = productive_date_end
                tmp['date_end'] = performance_date_end
                timeline.create(tmp)

    @api.multi
    def complete_workorders(self):
        """compare this method with the record_production() method of the mrp.workorder model"""

        workorders = self.production_id.workorder_ids
        for wo in workorders:

            # delete move_lots for the work order
            wo.active_move_line_ids.unlink()

            # update work order quantity produced
            wo.qty_produced += self.product_qty
            wo.final_lot_id = False

            # close the work order
            wo.write({'state': 'done', 'date_finished': fields.Datetime.now()})

        return True

    # Check Availability Button
    # Executes action_assign() method.  Adds all components to the
    # stock_move_lots table with done_wo=True.  If they are serialized, then
    # multiple rows are added at qty 1 to equal the total to be consumed.  The
    # lot_id is also populated with the next available serial number.  If there
    # is no routing, or if planning by work order is turned off, then the serial
    # number assignment is handled on the MO.

    # Plan Button
    # The Plan button creates work orders and adds lines in stock_move_lots,
    # setting the work order_id field as appropriate.  Only lines for tracked
    # components are added, with done_wo=False and quantity_done=1.  No guess
    # is made on which lot_id will be used; the lot_id field is left null.  If
    # the user specifies serial numbers on the MO, as described above, the
    # stock_move_lot records for the work order are unaffected.  The user can’t
    # complete the work order until specifying serials on the work order form.
    # Rumor has it that specifying serials in both places causes over-
    # consumption.  My understanding of the record_production() method supports
    # the rumor.

    # Register Lots --> do_plus()
    # When clicking the Register Lots button in the Consumed Materials list,
    # the user gets the view_stock_move_lots form.  The user can change the lot
    # to be consumed.  This form allows the user to accept the proposed serial
    # numbers (do_plus or set done to 1).  On Save, the quantity_done field of
    # the stock_move_lots records for this product are set to 1.  This only
    # applies to the records where done_wo=True. There is no update to
    # stock.move.lots records which are associated with work orders.
    # Note: the stock.move quantity_done field is computed from the
    # quantity_done field on stock.move.lots.

    # Produce Button
    # Starts the mrp.product.produce wizard which executes the do_produce()
    # method.  For untracked products, this method sets the qty_done field on
    # the stock moves to the quantity required/produced by the MO.  Serial
    # tracked products have quantities updated through the consume_line_ids
    # field (stock.move.lots).  The do_produce() method also calls the check
    # finished_move_lots() method, which sets up the lot traceability between
    # tracked components and tracked parents.  Note that when producing
    # multiple tracked products, each item of a given tracked component will be
    # tied to a different one of produced parents by the lot_produced_id field.


class MrpProductProduceLine(models.TransientModel):
    _name = "mrp.wo.produce.line"
    _description = "Record Production Line"

    product_produce_id = fields.Many2one('mrp.wo.produce')
    product_id = fields.Many2one('product.product', 'Product')
    product_tracking = fields.Selection(related="product_id.tracking", readonly=False)
    lot_id = fields.Many2one('stock.production.lot', 'Lot/Serial Number')
    qty_to_consume = fields.Float('To Consume', digits=dp.get_precision('Product Unit of Measure'))
    product_uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    qty_done = fields.Float('Consumed')
    move_id = fields.Many2one('stock.move')
    qty_reserved = fields.Float('Reserved')

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        """ When the user is encoding a produce line for a tracked product, we apply some logic to
        help him. This onchange will automatically switch `qty_done` to 1.0.
        """
        res = {}
        if self.product_id.tracking == 'serial':
            self.qty_done = 1
        return res

    @api.onchange('qty_done')
    def _onchange_qty_done(self):
        """ When the user is encoding a produce line for a tracked product, we apply some logic to
        help him. This onchange will warn him if he set `qty_done` to a non-supported value.
        """
        res = {}
        if self.product_id.tracking == 'serial' and self.qty_done:
            if float_compare(self.qty_done, 1.0, precision_rounding=self.move_id.product_id.uom_id.rounding) != 0:
                message = _('You can only process 1.0 %s of products with unique serial number.') % self.product_id.uom_id.name
                res['warning'] = {'title': _('Warning'), 'message': message}
        return res

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.product_uom_id = self.product_id.uom_id.id
