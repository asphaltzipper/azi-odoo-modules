# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round


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

    name = fields.Char(
        string="Name",
        compute='_compute_name',
        readonly=True)

    state = fields.Selection(
        selection=[('draft', 'New'),
                   ('imported', 'Imported'),
                   ('closed', 'Done'),
                   ('cancel', 'Canceled')],
        string="Closed",
        default='draft',
        required=True)

    work_date = fields.Datetime(
        string="Work Date",
        default=fields.Datetime.now(),
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
            rec.name = rec.work_user_id.name + ', ' + self.work_date[:10]

    @api.depends('detail_ids', 'total_hours', 'misc_hours')
    def _compute_time_match(self):
        for rec in self:
            detail_time = sum(rec.detail_ids.mapped('minutes_assigned')) / 60 or 0.0
            rounded_detail_time = float_round(detail_time, precision_digits=3)
            rounded_total_time = float_round(rec.total_hours, precision_digits=3)
            rec.time_match = rounded_detail_time == rounded_total_time

    @api.depends('detail_ids')
    def _compute_detail_time(self):
        for rec in self:
            rec.detail_time = sum(rec.detail_ids.mapped('minutes_assigned')) / 60 or 0.0

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
                detail.minutes_assigned = (self.total_hours-self.misc_hours) * 60 * detail_factors[detail.id] / (factor_sum or 1.0)
            else:
                detail.minutes_assigned = self.misc_hours/misc_count * 60

    def button_clear_import(self):
        self.ensure_one()
        self.detail_ids.unlink()
        self.state = 'draft'

    def button_apply_work(self):
        self.ensure_one()

        detail_time = sum(self.detail_ids.mapped('minutes_assigned')) / 60 or 0.0
        rounded_detail_time = float_round(detail_time, precision_digits=3)
        rounded_total_time = float_round(self.total_hours, precision_digits=3)
        if rounded_detail_time != rounded_total_time:
            raise UserError("Time assigned on detail lines ({} hours) doesn't sum to the total time on the batch ({} hours)".format(self.detail_time, self.total_hours))

        for detail in self.detail_ids.filtered(lambda r: r.production_id):
            mo = detail.production_id
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
                work.update({
                    'user_id': self.work_user_id.id,
                    'labor_date': self.work_date,
                    'labor_time': (detail.minutes_assigned/60)/wo_count,
                })
            produce_wiz.do_produce()
            mo.button_mark_done()

        self.state = 'closed'


class MfgWorkDetail(models.Model):
    _name = 'mfg.work.detail'

    header_id = fields.Many2one(
        comodel_name='mfg.work.header',
        string="Work Header",
        required=True)

    import_mfg_code = fields.Char(
        string="Imported Mfg Code",
        required=True,
        readonly=True)

    import_production_code = fields.Char(
        string="Imported Mfg Code",
        required=True,
        readonly=True)

    import_quantity = fields.Float(
        string="Completed Quantity",
        required=True,
        readonly=True)

    actual_quantity = fields.Float(
        string="Actual Quantity",
        required=True,
        default=0.0)

    production_id = fields.Many2one(
        comodel_name='mrp.production',
        string='Mfg Order')

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product')

    minutes_assigned = fields.Float(
        string="Assigned Minutes",
        default=0.0,
        help="Minutes of total time distributed to this production order")
