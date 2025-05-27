# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, Command, _
from odoo.exceptions import ValidationError


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    labor_ids = fields.One2many('mrp.production.labor', 'production_id', 'Labor Details')

    def action_confirm(self):
        res = super(MrpProduction, self).action_confirm()
        for production in self:
            labor_list = [Command.delete(labor.id) for labor in production.labor_ids]
            labor_lines = [Command.create({'workorder_id': wo.id, 'production_id': production.id,
                                           'labor_date': fields.Datetime.now()}) for wo in production.workorder_ids]
            if labor_lines:
                labor_list += labor_lines
            production.labor_ids = labor_list
        return res

    @staticmethod
    def check_labor_information(labor):
        if labor.filtered(lambda l: not l.employee_id or l.labor_time <= 0):
            raise ValidationError(_('You must specify user and hours in labor details!'))
        return True

    def create_workorder_labor(self):
        for production in self:
            MrpProduction.check_labor_information(production.labor_ids)
            production.workorder_ids.mapped('time_ids').unlink()
            productive_id = self.env['mrp.workcenter.productivity.loss'].search([('loss_type', '=', 'productive')],
                                                                                limit=1)
            if not productive_id:
                raise ValidationError(_("You need to define at least one productivity loss in the category "
                                        "'Productivity'. Create one from the Manufacturing app, menu: "
                                        "Configuration / Productivity Losses."))
            performance_id = self.env['mrp.workcenter.productivity.loss'].search([('loss_type', '=', 'performance')],
                                                                                 limit=1)
            if not performance_id:
                raise ValidationError(_("You need to define at least one productivity loss in the category "
                                        "'Performance'. Create one from the Manufacturing app, menu: "
                                        "Configuration / Productivity Losses."))
            timeline = self.env['mrp.workcenter.productivity']
            for labor in production.labor_ids:
                time_minutes = labor.labor_time * 60
                labor_vals = {
                    'workorder_id': labor.workorder_id.id,
                    'workcenter_id': labor.workorder_id.workcenter_id.id,
                    'user_id': labor.user_id.id,
                    'description': _('Time Tracking: ') + labor.user_id.name,
                    'date_start': labor.labor_date,
                    'date_end': fields.Datetime.from_string(labor.labor_date) + relativedelta(minutes=time_minutes),
                }
                if time_minutes + labor.workorder_id.duration <= labor.workorder_id.duration_expected:
                    tmp = labor_vals.copy()
                    tmp['loss_id'] = productive_id.id
                    timeline.create(tmp)
                elif labor.workorder_id.duration >= labor.workorder_id.duration_expected:
                    tmp = labor_vals.copy()
                    tmp['loss_id'] = performance_id.id
                    timeline.create(tmp)
                else:
                    productive_time = labor.workorder_id.duration_expected - labor.workorder_id.duration
                    performance_time = time_minutes - productive_time
                    productive_date_end = fields.Datetime.from_string(labor.labor_date) + relativedelta(minutes=productive_time)
                    performance_date_end = productive_date_end + relativedelta(minutes=performance_time)
                    tmp = labor_vals.copy()
                    tmp['loss_id'] = productive_id.id
                    tmp['date_end'] = productive_date_end
                    timeline.create(tmp)
                    tmp['loss_id'] = performance_id.id
                    tmp['date_start'] = productive_date_end
                    tmp['date_end'] = performance_date_end
                    timeline.create(tmp)

    def button_mark_done(self):
        if self.env.context.get('skip_immediate', False):
            self.create_workorder_labor()
        return super(MrpProduction, self).button_mark_done()


class MrpProductionLabor(models.Model):
    _name = "mrp.production.labor"
    _description = 'MO Labor Details'

    production_id = fields.Many2one('mrp.production', 'Manufacturing Order')
    workorder_id = fields.Many2one('mrp.workorder', 'Work Order')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    user_id = fields.Many2one('res.users', 'User', compute='_compute_user')
    labor_date = fields.Datetime('Date', default=fields.Datetime.now())
    labor_time = fields.Float('Hours')
    hours_expected = fields.Float('Standard', compute='_compute_hours_expected',)

    @api.depends('workorder_id')
    def _compute_hours_expected(self):
        for rec in self:
            rec.hours_expected = rec.workorder_id.duration_expected / 60

    @api.depends('workorder_id', 'employee_id')
    def _compute_user(self):
        for record in self:
            if record.employee_id:
                record.user_id = record.employee_id.sudo().user_id
            else:
                record.user_id = None
