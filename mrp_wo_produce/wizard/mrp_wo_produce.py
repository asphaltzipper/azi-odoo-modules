from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round


class MrpWoProduce(models.TransientModel):
    """
    This wizard is a loose copy of the mrp.product.produce wizard.  Extending
    that wizard to handle routings/workorders would make it too complex.

    This simplified wizard does not support changing the produced quantity.

    This module does not support adding/changing consumed material. It assumes
    that the mrp_change_material module is used for that. The
    mrp_change_material module should handle the case where the user adds
    consumed material with lot/serial tracking, and then processes the work
    orders manually.  We don't want the new moves to get canceled when
    completing the MO.

    Show a button to execute this wizard whenever there are work orders
    associated with this MO.  i.e. The button should only show after the user
    has clicked the Plan button.
    """

    _name = "mrp.wo.produce"
    _description = 'Produce MO with Workorders'

    production_id = fields.Many2one(
        comodel_name='mrp.production',
        string='Production',
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        related='production_id.product_id',
    )
    product_qty = fields.Float(
        string='Quantity',
        digits=dp.get_precision('Product Unit of Measure'),
        readonly=True)
    product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Unit of Measure',
        related='production_id.product_id.uom_id',
    )
    lot_id = fields.Many2one(
        comodel_name='stock.production.lot',
        string='Lot/Serial Number',
    )
    consume_line_ids = fields.One2many(
        comodel_name='mrp.wo.produce.comp_line',
        inverse_name='produce_id',
        string='Tracked Components')
    produce_line_ids = fields.One2many(
        comodel_name='mrp.wo.produce.by_line',
        inverse_name='produce_id',
        string='Tracked By-Products')
    work_line_ids = fields.One2many(
        comodel_name='mrp.wo.produce.work_line',
        inverse_name='produce_id',
        string="Work Order Labor",
    )
    product_tracking = fields.Selection(
        related="product_id.tracking",
        readonly=True,
    )

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
            return res

        serial_finished = (production.product_id.tracking == 'serial')
        todo_uom = production.product_uom_id
        produce_multi = float_compare(
            production.product_qty,
            1.0,
            precision_rounding=production.product_uom_id.rounding) != 0
        unit_uom = self.env.ref('uom.product_uom_unit')
        if serial_finished and (produce_multi or todo_uom != unit_uom):
            raise UserError("The Produce Workorders wizard can't handle"
                            " producing multiple serialized products. You will"
                            " have to process the work orders manually.")

        main_product_moves = production.move_finished_ids.filtered(
            lambda x: x.product_id.id == production.product_id.id)
        todo_quantity = production.product_qty - sum(main_product_moves.mapped('quantity_done'))
        todo_quantity = todo_quantity if (todo_quantity > 0.0) else 0.0

        res.update({
            'production_id': production.id,
            'product_id': production.product_id.id,
            'product_uom_id': todo_uom.id,
            'product_qty': todo_quantity,
        })
        return res

    @api.onchange('production_id')
    def _onchange_production_id(self):
        self.load_lines()
        main_product_moves = self.production_id.move_finished_ids.filtered(
            lambda x: x.product_id.id == self.production_id.product_id.id)
        todo_quantity = self.production_id.product_qty - sum(main_product_moves.mapped('quantity_done'))
        todo_quantity = todo_quantity if (todo_quantity > 0.0) else 0.0
        self.update({
            'product_qty': todo_quantity,
        })

    @api.model
    def load_lines(self):
        """
        We only display and process moves for tracked products.

        For each stock move, one or more lines will have already been
        generated when clicking the Plan button. This happens for all raw
        moves, including those added by the mrp_change_material module. It
        happens in these methods:
          - mrp.production._workorders_create()
          - mrp.workorder._generate_lot_ids()

        For the same move, another set of lines is generated when the user
        clicks the button Check Availability.  A comparison of values between
        these stock move lines follows:

              Field      | Check Avail Button | Plan Button
        -----------------+--------------------+-------------
         product_uom_qty |                  1 |           0
         qty_done        |                  0 |           1
         lot_id          |   <fifo available> |        NULL
         product_qty     |                  1 |           0
         done_wo         |                  1 |           0

        We cannot reliably select and operate on these stock move lines, based
        on any searchable criteria. We also have to consider that the user may
        have modified these stock move lines. As such, we will attempt to
        delete them later, and generate new lines. For now, we extract the
        useful data they contain.
        """

        mo = self.production_id

        consume_lines = []
        for move in mo.move_raw_ids.filtered(
                lambda m: m.state not in ('done', 'cancel')
                          and m.product_id.tracking != 'none'):
            qty = move.product_uom_qty - move.quantity_done
            res_qty = move.reserved_availability - move.quantity_done
            res_lots = move.move_line_ids.filtered(lambda x: x.state not in ['done', 'cancel']).mapped('lot_id').ids
            if move.product_id.tracking == 'serial':
                while float_compare(qty, 0.0, precision_rounding=move.product_uom.rounding) > 0:
                    consume_lines.append({
                        'move_id': move.id,
                        'qty_to_consume': 1.0,
                        'qty_done': res_lots and 1 or 0,
                        'lot_id': res_lots and res_lots.pop() or False,
                        'product_id': move.product_id.id,
                        'qty_reserved': res_qty,
                    })
                    qty -= 1
                    res_qty = res_qty >= 1 and res_qty - 1 or 0
            else:
                # TODO: using read_group, get lot qty when multiple reserved
                consume_lines.append({
                    'move_id': move.id,
                    'qty_to_consume': qty,
                    'qty_done': res_lots and qty or 0,
                    'lot_id': res_lots and res_lots.pop() or False,
                    'product_id': move.product_id.id,
                    'qty_reserved': res_qty,
                })
        self.consume_line_ids = [(5,)] + [(0, 0, x) for x in consume_lines]

        # it is possible the user created stock move lines for by-products
        produce_lines = []
        for move in mo.move_finished_ids.filtered(
                lambda m: m.state not in ('done', 'cancel') and
                          m.product_id.tracking != 'none' and
                          m.product_id != mo.product_id):
            qty = move.product_uom_qty - move.quantity_done
            res_qty = move.reserved_availability - move.quantity_done
            res_lots = move.move_line_ids.filtered(lambda x: x.state not in ['done', 'cancel']).mapped('lot_id').ids
            if move.product_id.tracking == 'serial':
                while float_compare(qty, 0.0, precision_rounding=move.product_uom.rounding) > 0:
                    produce_lines.append({
                        'move_id': move.id,
                        'qty_to_produce': 1.0,
                        'qty_done': res_lots and 1 or 0,
                        'lot_id': res_lots and res_lots.pop() or False,
                        'product_id': move.product_id.id,
                        'qty_reserved': res_qty,
                    })
                    qty -= 1
                    res_qty = res_qty >= 1 and res_qty - 1 or 0
            else:
                # TODO: using read_group, get lot qty when multiple reserved
                produce_lines.append({
                    'move_id': move.id,
                    'qty_to_produce': qty,
                    'qty_done': res_lots and qty or 0,
                    'lot_id': res_lots and res_lots.pop() or False,
                    'product_id': move.product_id.id,
                    'qty_reserved': res_qty,
                })
        self.produce_line_ids = [(5,)] + [(0, 0, x) for x in produce_lines]

        work_lines = [{'workorder_id': wo.id} for wo in mo.workorder_ids]
        self.work_line_ids = [(5,)] + [(0, 0, x) for x in work_lines]

    @api.multi
    def do_produce(self):
        self.update_work_time()
        self.complete_workorders()
        self.prepare_finished_moves()
        self.production_id.button_mark_done()
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def update_work_time(self):
        """this method has been adapted from mrp.workorder methods button_start() and end_previous()"""

        # verify all work orders have time reported
        reported_workorders = self.work_line_ids.mapped('workorder_id')
        unreported_workorder_ids = self.production_id.workorder_ids\
            .filtered(lambda x: x.id not in reported_workorders.ids and x.duration_expected > 0.0).ids
        work_summary = self.work_line_ids.read_group(
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
        if self.work_line_ids.filtered(lambda x: not x.user_id or not x.labor_date):
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
        for work in self.work_line_ids:
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
        last_workorder = self.production_id.workorder_ids.filtered(lambda x: not x.next_work_order_id)[0]
        # delete all existing move lines
        self.consume_line_ids.mapped('move_id.move_line_ids').\
            filtered(lambda x: x.state not in ['done', 'cancel']).unlink()
        # create new move lines
        for line in self.consume_line_ids:
            if not line.lot_id:
                raise UserError(_('Please enter a lot or serial number for component %s !' % line.product_id.display_name))
            if float_compare(
                    line.qty_to_consume,
                    line.qty_done,
                    precision_rounding=line.product_id.uom_id.rounding) != 0:
                raise UserError(_('Please correct Consumed quantity for lot %s !' % line.lot_id.display_name))
            line.move_id.move_line_ids.create({
                'move_id': line.move_id.id,
                'lot_id': line.lot_id.id,
                'lot_produced_id': self.lot_id.id or False,
                'product_uom_qty': 0,
                'product_uom_id': line.move_id.product_uom.id,
                'qty_done': line.qty_done,
                'production_id': self.production_id.id,
                'workorder_id': line.move_id.workorder_id.id or last_workorder.id,
                'product_id': line.product_id.id,
                'done_wo': False,
                'location_id': line.move_id.location_id.id,
                'location_dest_id': line.move_id.location_dest_id.id,
            })
            # line.move_id._action_assign()

        for wo in self.production_id.workorder_ids:
            if self.product_id.tracking != 'none':
                wo.final_lot_id = self.lot_id
            # pass all quality checks
            for check in wo.check_ids:
                check.do_pass()
            wo.record_production()

        return True

    @api.multi
    def prepare_finished_moves(self):
        # main finished move
        produce_move = self.production_id.move_finished_ids.filtered(
            lambda x: x.product_id == self.product_id and x.state not in ('done', 'cancel'))
        if not produce_move:
            raise UserError(_("The finished move is already done or canceled."))
        if produce_move.product_id.tracking != 'none':
            if not self.lot_id:
                raise UserError(_('You need to provide a lot for the finished product.'))
            # The finished move line is created when completing the workorder
            # We are only producing quantity of one
            # We checked producing quantity at the beginning
            finished_line = produce_move.move_line_ids.filtered(
                lambda x: x.lot_id == self.lot_id)
            if not finished_line:
                raise UserError(_("Something went wrong with processing the"
                                  " finished product move. This may result from"
                                  " failing to complete the workorders."))
            if len(finished_line) > 1:
                raise UserError(_('You cannot produce multiple lots with this wizard.'))
            finished_line.update({
                'qty_done': finished_line.product_uom_qty,
                'lot_id': self.lot_id.id,
            })
        else:
            produce_move._set_quantity_done(self.product_qty)
            if len(produce_move.move_line_ids) > 1:
                # apparently, the work orders created multiple move lines
                # we will delete them all, and then set the quantity done
                produce_move.move_line_ids.unlink()
                produce_move._set_quantity_done(self.product_qty)

        # by-products with tracking
        # delete all existing move lines
        self.produce_line_ids.mapped('move_id.move_line_ids').\
            filtered(lambda x: x.state not in ['done', 'cancel']).unlink()
        # create new move lines
        for line in self.produce_line_ids:
            if not line.lot_id:
                raise UserError(_('Please enter a lot or serial number for by-product %s !' % line.product_id.display_name))
            if float_compare(
                    line.qty_to_produce,
                    line.qty_done,
                    precision_rounding=line.product_id.uom_id.rounding) != 0:
                raise UserError(_('Please correct Produced quantity for lot %s !' % line.lot_id.display_name))
            line.move_id.move_line_ids.create({
                'move_id': line.move_id.id,
                'lot_id': line.lot_id.id,
                'product_uom_qty': line.qty_done,
                'product_uom_id': line.move_id.product_uom.id,
                'qty_done': line.qty_done,
                'production_id': self.production_id.id,
                'product_id': line.product_id.id,
                'location_id': line.move_id.location_id.id,
                'location_dest_id': line.move_id.location_dest_id.id,
            })

        # by-products without tracking
        by_product_moves = self.production_id.move_finished_ids.filtered(
            lambda x: x.product_id != self.product_id
                      and x.state not in ('done', 'cancel')
                      and x.product_id.tracking == 'none')
        for by_move in by_product_moves:
            # TODO: is this necessary?
            if len(produce_move.move_line_ids) > 1:
                raise UserError(_("There are multiple move lines for by-product %s" % by_move.product_id.display_name))
            by_move.quantity_done = by_move.product_uom_qty

        # TODO: pass all quality checks
        return True


class MrpProductProduceCompLine(models.TransientModel):
    _name = "mrp.wo.produce.comp_line"
    _description = "Tracked Component Line"

    produce_id = fields.Many2one(
        comodel_name='mrp.wo.produce',
        required=True,
        ondelete='cascade',
    )
    move_id = fields.Many2one(
        comodel_name='stock.move',
        required=True,
        ondelete='cascade',
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        related='move_id.product_id',
    )
    product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Unit of Measure',
        related='move_id.product_id.uom_id',
        ondelete='cascade',
    )
    qty_to_consume = fields.Float(
        string='To Consume',
        digits=dp.get_precision('Product Unit of Measure'),
        required=True,
    )
    qty_done = fields.Float(
        string='Consumed',
        required=True,
    )
    qty_reserved = fields.Float(
        string='Reserved',
        required=True,
    )
    lot_id = fields.Many2one(
        comodel_name='stock.production.lot',
        string='Lot/Serial Number',
    )

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        """ When the user is encoding a produce line for a tracked product, we apply some logic to
        help him. This onchange will automatically switch `qty_done` to 1.0.
        """
        res = {}
        if self.product_id.tracking == 'serial':
            if self.lot_id:
                self.qty_done = 1
            else:
                self.qty_done = 0
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


class MrpProductProduceByLine(models.TransientModel):
    _name = "mrp.wo.produce.by_line"
    _description = "Tracked By-Product Line"

    produce_id = fields.Many2one(
        comodel_name='mrp.wo.produce',
        required=True,
        ondelete='cascade',
    )
    move_id = fields.Many2one(
        comodel_name='stock.move',
        required=True,
        ondelete='cascade',
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        related='move_id.product_id',
    )
    product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Unit of Measure',
        related='move_id.product_id.uom_id',
        ondelete='cascade',
    )
    qty_to_produce = fields.Float(
        string='To Produce',
        digits=dp.get_precision('Product Unit of Measure'),
        required=True,
    )
    qty_done = fields.Float(
        string='Produced',
        required=True,
    )
    qty_reserved = fields.Float(
        string='Reserved',
        required=True,
    )
    lot_id = fields.Many2one(
        comodel_name='stock.production.lot',
        string='Lot/Serial Number',
    )

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        """ When the user is encoding a produce line for a tracked product, we apply some logic to
        help him. This onchange will automatically switch `qty_done` to 1.0.
        """
        res = {}
        if self.product_id.tracking == 'serial':
            if self.lot_id:
                self.qty_done = 1
            else:
                self.qty_done = 0
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


class MrpWoProduceWorkLine(models.TransientModel):
    _name = "mrp.wo.produce.work_line"
    _description = 'Workorder Labor Details'

    produce_id = fields.Many2one(
        comodel_name='mrp.wo.produce',
        required=True,
    )
    production_id = fields.Many2one(
        comodel_name='mrp.production',
        related='produce_id.production_id',
    )
    workorder_id = fields.Many2one(
        comodel_name='mrp.workorder',
        string="Work Order",
        required=True,
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string="User",
    )
    user_ids = fields.Many2many(
        'res.users',
        compute='_compute_user_ids',
    )
    labor_date = fields.Datetime(
        string="Date",
    )
    labor_time = fields.Float(
        string='Hours',
    )
    hours_expected = fields.Float(
        string='Standard',
        compute='_compute_hours_expected',
    )

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
