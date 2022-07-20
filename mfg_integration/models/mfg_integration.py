# -*- coding: utf-8 -*-
import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round
import logging
_logger = logging.getLogger(__name__)


class MfgGauge(models.Model):
    _name = 'mfg.gauge'
    _description = 'Sheet Metal Thickness Gauge'

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
    _description = 'Sheet Metal Material Types'

    name = fields.Char(
        string="Material")

    gauge_ids = fields.Many2many(
        comodel_name='mfg.gauge',
        string="Valid Gauges")


class MfgWorkHeader(models.Model):
    _name = 'mfg.work.header'
    _description = 'Imported MFG Work Batch'
    _order = 'work_date desc, work_user_id'

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Name must be unique"),
        ('file_name_uniq', 'unique (file_name)', "File name must be unique"),
    ]

    name = fields.Char(
        string="Name",
        required=True,
        default="Empty: "+str(fields.Date.today()),
        readonly=True)

    file_name = fields.Char(
        string="File Name",
        readonly=True)

    project_name = fields.Char(
        string="Project Name",
        readonly=True)

    sheet_number = fields.Integer(
        string="Sheet Num",
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
    product_error = fields.Boolean(
        string='Error',
        compute='_compute_error',
        store=True,
        required=True,
        default=False,
        help="Product parameters are missing/incomplete/invalid. "
             "Check the BOM, Routing, and Fabrication Info.")

    material = fields.Char(
        string='Material',
        readonly=True)
    thickness = fields.Char(
        string='Thickness',
        readonly=True)
    sheet_x = fields.Float(
        string='SheetX',
        readonly=True)
    sheet_y = fields.Float(
        string='SheetY',
        readonly=True)
    utilization = fields.Float(
        string='Utilization',
        readonly=True)
    runtime_s = fields.Float(
        string='Runtime',
        readonly=True,
        help="Processing time in seconds")
    number_sheets = fields.Integer(
        string='Sheets',
        required=True,
        default=1,
        readonly=True,
        help="Adding to the number of sheets will multiply the number parts produced")
    thumbnail = fields.Binary(
        string="Thumbnail",
        attachment=True,
        readonly=True)

    @api.depends('detail_ids', 'total_hours', 'misc_hours')
    def _compute_time_match(self):
        for rec in self:
            detail_time = sum(rec.detail_ids.mapped('minutes_assigned')) / 60 or 0.0
            rec.time_match = abs(detail_time - rec.total_hours) < 0.1

    @api.depends('detail_ids')
    def _compute_error(self):
        for rec in self:
            rec.product_error = rec.detail_ids.filtered(lambda x: x.product_error)

    @api.depends('detail_ids')
    def _compute_detail_time(self):
        for rec in self:
            rec.detail_time = sum(rec.detail_ids.mapped('minutes_assigned')) / 60 or 0.0

    def button_reassign_orders(self):
        self.ensure_one()
        self.detail_ids._compute_error()
        self.detail_ids.reassign_orders()
        self.write({'state': 'assigned'})

    def button_distribute_time(self):
        self.ensure_one()
        # split and assign time to detail lines
        factor_sum = 0.0
        misc_count = 0
        detail_factors = {}
        self.detail_ids.update({'minutes_assigned': 0.0})
        for detail in self.detail_ids.filtered(lambda x: x.actual_quantity > 0.0 and not x.product_error):
            if detail.product_id:
                nt = detail.product_id.rm_product_id.gauge_id.nominal_thk
                cl = detail.product_id.cutting_length_outer + detail.product_id.cutting_length_inner or 1.0
                bc = detail.product_id.bend_count
                cc = detail.product_id.cut_out_count + 1
                time_factor = bc + nt * (cc + cl)
                time_factor *= detail.actual_quantity
            else:
                time_factor = 0.0
                misc_count += 1
            detail_factors[detail.id] = time_factor
            factor_sum += time_factor

        for detail in self.detail_ids.filtered(lambda x: x.actual_quantity > 0.0 and not x.product_error):
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
        self.name = "Empty: " + fields.Date.today()
        self.file_name = False

    def button_apply_work(self):
        self.ensure_one()

        detail_time = sum(self.detail_ids.mapped('minutes_assigned')) / 60 or 0.0
        rounded_detail_time = float_round(detail_time, precision_digits=2)
        rounded_total_time = float_round(self.total_hours, precision_digits=2)
        if abs(detail_time - self.total_hours) > 0.1:
            raise UserError(
                "Time assigned on detail lines ({} hours) doesn't sum to the "
                "total time on the batch ({} hours)".format(
                    rounded_detail_time, rounded_total_time))

        # check for canceled or completed orders
        comp_lines = self.detail_ids.filtered(
            lambda x: x.production_state in ('done', 'cancel'))
        if comp_lines:
            message = "The following orders have already been completed (or " \
                      "canceled).  You should reassign orders.\n"
            message += ", ".join(comp_lines.mapped('production_id.name'))
            raise UserError(message)

        for detail in self.detail_ids.filtered(lambda r: r.production_id):
            mo = detail.production_id
            _logger.info(mo.name)
            if not mo.product_id.id == detail.product_id.id:
                raise UserError(
                    "{} does not match the product on {} ({})".format(
                        detail.product_id.default_code,
                        mo.name,
                        mo.product_id.default_code))
            if mo.state == 'confirmed':
                mo.button_plan()
            if detail.actual_quantity != mo.product_qty:
                change_wiz = self.env['change.production.qty'].create(
                    {'mo_id': mo.id, 'product_qty': detail.actual_quantity})
                change_wiz.change_prod_qty()
            ctx = dict(self.env.context)
            ctx['default_production_id'] = mo.id
            produce_wiz = self.env['mrp.wo.produce'].with_context(ctx).create({'production_id': mo.id})
            produce_wiz.load_lines()

            # divide time evenly across workorders
            wo_count = len(produce_wiz.production_id.workorder_ids)
            for work in produce_wiz.work_line_ids:
                if detail.minutes_assigned <= 1.0:
                    raise UserError("Work time cannot be less than 1 minute per manufacturing order")
                labor_time = (detail.minutes_assigned/60)/wo_count
                work.update({
                    'user_id': self.work_user_id.id,
                    'labor_date': datetime.datetime.combine(self.work_date, datetime.datetime.min.time()),
                    'labor_time': labor_time,
                })
            produce_wiz.do_produce()

        self.state = 'closed'

    @api.model
    def change_sheets(self, new_count):
        """Multiply quantity produced by the number of sheets."""
        self.ensure_one()

        for detail in self.detail_ids:
            detail.actual_quantity = detail.import_quantity * new_count
        self.number_sheets = new_count


class MfgWorkDetail(models.Model):
    _name = 'mfg.work.detail'
    _description = 'MFG Work Batch Detail Lines'
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

    product_error = fields.Boolean(
        string='Error',
        compute='_compute_error',
        store=True,
        required=True,
        default=False,
        help="Product parameters are missing/incomplete/invalid. "
             "Check the BOM, Routing, and Fabrication Info.")

    bbox_x = fields.Float(
        string="X",
        required=True,
        default=0.0)
    bbox_y = fields.Float(
        string="Y",
        required=True,
        default=0.0)
    part_num = fields.Integer(
        string="Part Num",
        readonly=True)

    @api.depends('product_id')
    def _compute_error(self):
        for rec in self:

            rec.product_error = rec.product_id and (
                        not rec.product_id.bom_ids
                        or not rec.product_id.bom_ids[0].routing_id
                        or not rec.product_id.cutting_length_outer +
                               rec.product_id.cutting_length_inner +
                               rec.product_id.cut_out_count +
                               rec.product_id.bend_count > 0.0001)

    @api.multi
    def reassign_orders(self):
        header = self[0].header_id

        # warn the user about products with errors
        error_products = self.filtered(lambda x: x.product_error).mapped('product_id')
        if error_products:
            message = "The following products are missing BOMs or Routings " \
                      "or MFG data:\n {}".format(",".join(error_products.mapped('default_code')))
            self.env.user.notify_warning(message=message, title="MRP Complete", sticky=True)

        products = self.filtered(lambda x: not x.product_error).mapped('product_id')
        for product in products:

            # check for open MOs
            mos = self.env['mrp.production'].search(
                [('product_id', '=', product.id), ('state', 'not in', ['done', 'cancel'])],
                order='date_planned_start')
            if not mos:
                mos = self.env['mrp.production'].create({
                    'product_id': product.id,
                    'product_uom_id': product.uom_id.id,
                    'product_qty': 1,
                    'bom_id': product.bom_ids and product.bom_ids.ids[0],
                })

            # merge duplicate product lines
            lines = self.search([('header_id', '=', header.id), ('product_id', '=', product.id)])
            line = lines[0]
            qty_to_assign = sum(lines.mapped('actual_quantity'))
            qty_imported = sum(lines.mapped('import_quantity'))
            production_codes = ",".join(set(
                lines.filtered(lambda x: x.import_production_code).mapped('import_production_code')))
            if len(lines) > 1:
                lines[1:].unlink()
            line.import_quantity = qty_imported
            line.import_production_code = production_codes

            # check if we produced any
            if qty_to_assign <= 0.0:
                # zero quantity produced
                line.production_id = False
                continue

            # get the over-production quantity...
            # ie whether we produced more (+) product than we have orders for
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
            # we now add new lines for assigning quantity to other open MOs
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
                raise UserError("Failed to assign the full production quantity"
                                " for product {}".format(product.display_name))
