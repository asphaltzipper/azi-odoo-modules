# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round
import logging
_logger = logging.getLogger(__name__)


class MfgGauge(models.Model):
    _name = 'mfg.gauge'

    name = fields.Char(
        string='Name',
        required=True)

    laser_code = fields.Char(
        string='Laser Code',
        required=True)

    nominal_thk = fields.Float(
        string='Nominal Thickness',
        required=True)


class MfgMaterial(models.Model):
    _name = 'mfg.material'

    name = fields.Char(
        string="Material")

    gauge_ids = fields.Many2many(
        comodel_name='mfg.gauge',
        string="Valid Gauges")


class MfgWorkHeader(models.Model):
    _name = 'mfg.work.header'
    _order = 'work_date desc, work_user_id'

    name = fields.Char(
        string="Name",
        compute='_compute_name',
        readonly=True)

    state = fields.Selection(
        selection=[('draft', 'New'),
                   ('imported', 'Imported'),
                   ('assigned', 'Assigned'),
                   ('closed', 'Done'),
                   ('cancel', 'Canceled')],
        string="Closed",
        default='draft',
        required=True)

    work_date = fields.Date(
        string="Work Date",
        default=fields.Date.today(),
        required=True)

    work_user_id = fields.Many2one(
        comodel_name='res.users',
        string="Work User",
        required=True)

    total_hours = fields.Float(
        string="Total Hours",
        required=True)

    misc_hours = fields.Float(
        string="Misc Hours",
        required=True)

    detail_ids = fields.One2many(
        comodel_name='mfg.work.detail',
        inverse_name='header_id')

    detail_time = fields.Float(
        string="Assigned Time",
        compute='_compute_detail_time',
        readonly=True,
        help="Time assigned to detail lines, in hours")

    time_match = fields.Boolean(
        compute='_compute_time_match',
        readonly=True)

    @api.depends('work_date', 'work_user_id')
    def _compute_name(self):
        for rec in self:
            rec.name = self.work_date + ', ' + rec.work_user_id.name

    @api.depends('detail_ids', 'total_hours', 'misc_hours')
    def _compute_time_match(self):
        for rec in self:
            detail_time = sum(rec.detail_ids.mapped('minutes_assigned')) / 60 or 0.0
            rounded_detail_time = float_round(detail_time, precision_digits=2)
            rounded_total_time = float_round(rec.total_hours, precision_digits=2)
            rec.time_match = rounded_detail_time == rounded_total_time

    @api.depends('detail_ids')
    def _compute_detail_time(self):
        for rec in self:
            rec.detail_time = sum(rec.detail_ids.mapped('minutes_assigned')) / 60 or 0.0

    def button_reassign_orders(self):
        self.ensure_one()
        self.detail_ids.reassign_orders()
        self.write({'state': 'assigned'})

    def button_distribute_time(self):
        self.ensure_one()
        # split and assign time to detail lines
        factor_sum = 0.0
        misc_count = 0
        detail_factors = {}
        for detail in self.detail_ids:
            detail.minutes_assigned = 0.0
            if detail.product_id:
                t = detail.product_id.rm_product_id.gauge_id.nominal_thk
                l = detail.product_id.cutting_length_outer + detail.product_id.cutting_length_inner or 1.0
                b = detail.product_id.bend_count
                c = detail.product_id.cut_out_count + 1
                time_factor = b + t * (c + l)
                time_factor *= detail.actual_quantity
            else:
                time_factor = 0.0
                misc_count += 1
            detail_factors[detail.id] = time_factor
            factor_sum += time_factor

        for detail in self.detail_ids:
            if detail.product_id:
                minutes = (self.total_hours-self.misc_hours) * 60 * detail_factors[detail.id] / (factor_sum or 1.0)
                detail.minutes_assigned = minutes >= 1.1 and minutes or 1.1
            else:
                minutes = self.misc_hours/misc_count * 60
                detail.minutes_assigned = minutes

    def button_clear_import(self):
        self.ensure_one()
        self.detail_ids.unlink()
        self.state = 'draft'

    def button_apply_work(self):
        self.ensure_one()

        detail_time = sum(self.detail_ids.mapped('minutes_assigned')) / 60 or 0.0
        rounded_detail_time = float_round(detail_time, precision_digits=2)
        rounded_total_time = float_round(self.total_hours, precision_digits=2)
        if rounded_detail_time != rounded_total_time:
            raise UserError("Time assigned on detail lines ({} hours) doesn't sum to the total time on the batch ({} hours)".format(rounded_detail_time, rounded_total_time))

        for detail in self.detail_ids.filtered(lambda r: r.production_id):
            mo = detail.production_id
            _logger.info(mo.name)
            if not mo.product_id.id == detail.product_id.id:
                raise UserError("{} does not match the product on {} ({})".format(detail.product_id.default_code, mo.name, mo.product_id.default_code))
            if not mo.state == 'planned':
                raise UserError("MO must be in state 'Planned': {}".format(mo.name))
            if detail.actual_quantity != mo.product_qty:
                change_wiz = self.env['change.production.qty'].create({'mo_id': mo.id, 'product_qty': detail.actual_quantity})
                change_wiz.change_prod_qty()
            ctx = dict(self.env.context)
            ctx['default_production_id'] = mo.id
            produce_wiz = self.env['mrp.wo.produce'].with_context(ctx).create({'production_id': mo.id})

            # divide time evenly across workorders
            produce_wiz.load_work()
            wo_count = len(produce_wiz.work_ids)
            for work in produce_wiz.work_ids:
                if detail.minutes_assigned <= 1.0:
                    raise UserError("Work time cannot be less than 1 minute per manufacturing order")
                labor_time = (detail.minutes_assigned/60)/wo_count
                work.update({
                    'user_id': self.work_user_id.id,
                    'labor_date': self.work_date,
                    'labor_time': labor_time,
                })
            produce_wiz.do_produce()
            mo.button_mark_done()

        self.state = 'closed'


class MfgWorkDetail(models.Model):
    _name = 'mfg.work.detail'
    _order = 'product_id, production_id, import_mfg_code'

    header_id = fields.Many2one(
        comodel_name='mfg.work.header',
        string="Work Header",
        required=True,
        ondelete='cascade',
        readonly=True)

    import_mfg_code = fields.Char(
        string="Import P/N",
        readonly=True)

    import_production_code = fields.Char(
        string="Import MO",
        readonly=True)

    import_quantity = fields.Float(
        string="Import Qty",
        required=True,
        default=0.0,
        readonly=True)

    actual_quantity = fields.Float(
        string="Actual Qty",
        required=True,
        default=0.0)

    production_id = fields.Many2one(
        comodel_name='mrp.production',
        string='Mfg Order',
        ondelete='set null')

    production_state = fields.Selection([
        ('confirmed', 'Confirmed'),
        ('planned', 'Planned'),
        ('progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')],
        string='State',
        related='production_id.state',
        readonly=True,
        store=True)

    order_qty = fields.Float(
        string='Order Qty',
        related='production_id.product_qty',
        readonly=True)

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        ondelete='set null')

    minutes_assigned = fields.Float(
        string="Assigned Minutes",
        default=0.0,
        help="Minutes of total time distributed to this production order")

    @api.multi
    def reassign_orders(self):
        header = self[0].header_id
        # check for canceled or completed orders
        comp_lines = self.filtered(lambda x: x.production_state in ('done', 'cancel'))
        if comp_lines:
            message = "The following orders have already been completed (or " \
                      "canceled).  Fix them before reassigning orders.\n"
            message += ", ".join(comp_lines.mapped('production_id.name'))
            raise UserError(message)

        products = self.mapped('product_id')
        for product in products:

            # check for open MOs
            mos = self.env['mrp.production'].search(
                [('product_id', '=', product.id), ('state', '=', 'planned')],
                order='date_planned_start')
            if not mos:
                continue

            # merge duplicate product lines
            lines = self.search([('header_id', '=', header.id), ('product_id', '=', product.id)])
            line = lines[0]
            qty_to_assign = sum(lines.mapped('actual_quantity'))
            qty_imported = sum(lines.mapped('import_quantity'))
            production_codes = ",".join(set(lines.filtered(lambda x: x.import_production_code).mapped('import_production_code')))
            if len(lines) > 1:
                lines[1:].unlink()
            line.import_quantity = qty_imported
            line.import_production_code = production_codes

            # get the over production quantity...
            # whether we produced more (+) product than we have orders for
            qty_remaining = max(0.0, qty_to_assign - sum(mos.mapped('product_qty')))

            # first assign quantity to the highest priority MO
            # including any over production
            line.production_id = mos[0].id
            line.actual_quantity = min(qty_to_assign, mos[0].product_qty + qty_remaining)
            qty_to_assign -= line.actual_quantity

            if qty_to_assign <= 0.0:
                # no more quantity to assign for this product
                continue

            # we should only get here if there are more open MOs and more quantity to assign
            # add new lines for assigning quantity to other open MOs
            for mo in mos[1:]:
                if qty_to_assign <= 0.0:
                    break
                line.create({
                    'header_id': line.header_id.id,
                    'product_id': product.id,
                    'production_id': mo.id,
                    'actual_quantity': min(qty_to_assign, mo.product_qty),
                })
                qty_to_assign -= min(qty_to_assign, mo.product_qty)

            if qty_to_assign:
                raise UserError("Failed to assign the full production quantity for product {}".format(product.display_name))
            # self._cr.commit()
