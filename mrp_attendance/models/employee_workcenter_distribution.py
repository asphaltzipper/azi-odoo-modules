import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta


class EmployeeWorkcenterDistribution(models.Model):
    _name = "employee.workcenter.distribution"
    _description = "Employee Workcenter Attendance Distribution"
    _order = "employee_id, start_date desc"

    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Employee",
        required=True,
        ondelete="cascade",
    )
    start_date = fields.Date(
        string="Start Date",
        required=True,
    )
    end_date = fields.Date(
        string="End Date",
    )
    line_ids = fields.One2many(
        comodel_name="employee.workcenter.distribution.line",
        inverse_name="ewd_id",
        string="Distribution Lines",
    )
    total_distribution = fields.Integer(
        string="Total Distribution",
        compute="_compute_total_distribution",
    )

    @api.constrains('employee_id', 'start_date', 'end_date')
    def _constrain_dates(self):
        # don't allow distributions for the same employee to have overlapping date ranges
        # TODO: check for distributions starting/ending in same period, but not overlapping
        # http://mysirg.org/convert-infix-to-prefix-notation
        # infix notation: a&b&((c&d)|(e&f)|(g&h))
        # prefix notation: &&ab||&cd&ef&gh
        # since & is the default operator, simplify: ab||&cd&ef&gh
        for rec in self:
            end_date = rec.end_date or datetime.date.today() + relativedelta(years=100)
            dom = [
                ('id', '!=', rec.id),
                ('employee_id', '=', rec.employee_id.id),
                '|',
                '|',
                '|',
                '&',
                # others with start_date bracketed by this start/end
                ('start_date', '>=', rec.start_date),
                ('start_date', '<=', end_date),
                '&',
                # others with end_date bracketed by this start/end
                ('end_date', '>=', rec.start_date),
                ('end_date', '<=', end_date),
                '&',
                # others open ended and starting before this ends
                ('end_date', '=', False),
                ('start_date', '<=', end_date),
                '&',
                # others completely containing this range
                ('end_date', '>=', end_date),
                ('start_date', '<=', rec.start_date),
            ]
            overlapping = rec.search(dom)
            if overlapping:
                raise ValidationError("The dates for this distribution overlap another.")

    @api.constrains('employee_id', 'line_ids')
    def _constrains_distribution_total(self):
        employee_dists = self.env['employee.workcenter.distribution.line']._read_group(
            domain=[('ewd_id', 'in', self.ids)],
            fields=['distribution'],
            groupby=['ewd_id'],
        )
        invalid_dists = {x['ewd_id'][0]: x['distribution'] for x in employee_dists if x['distribution'] > 100}
        if not len(invalid_dists):
            return
        ewd_ids = list(invalid_dists.keys()) or []
        messages = []
        for rec in self.browse(ewd_ids):
            messages.append(_(
                "%s %s - %s (%s%%)",
                rec.employee_id.name,
                rec.start_date.strftime("%Y-%m-%d"),
                rec.end_date.strftime("%Y-%m-%d"),
                rec.total_distribution,
            ))
        raise UserError(_(
            "Invalid employee workcenter distribution:\n%s",
            "\n".join(messages),
        ))

    def _compute_total_distribution(self):
        employee_dists = self.env['employee.workcenter.distribution.line']._read_group(
            domain=[('ewd_id', 'in', self.ids)],
            fields=['distribution'],
            groupby=['ewd_id'],
        )
        dists = {x['ewd_id'][0]: x['distribution'] for x in employee_dists}
        for rec in self:
            rec.total_distribution = dists.get(rec.id, 0)


class EmployeeWorkcenterDistributionLine(models.Model):
    _name = 'employee.workcenter.distribution.line'
    _description = "Employee Workcenter Attendance Distribution Line"
    _order = "distribution desc"
    _sql_constraints = [
        (
            'check_distribution_range',
            'CHECK(distribution > 0 and distribution <= 100)',
            'Percent Distribution must be between 1 and 100.'
        ),
    ]

    name = fields.Char(
        string="Name",
        compute="_compute_name",
    )
    ewd_id = fields.Many2one(
        comodel_name="employee.workcenter.distribution",
        string="Dist Group",
        required=True,
        ondelete="cascade",
    )
    workcenter_id = fields.Many2one(
        comodel_name="mrp.workcenter",
        string="Workcenter",
        required=True,
        ondelete="cascade",
    )
    distribution = fields.Integer(
        string="Percent Distribution",
        default=100,
        help="Percentage of attendance time assigned in "
             "this workcenter (a number between 1 and 100)",
    )

    def _compute_name(self):
        for rec in self:
            rec.name = _("%s (%s%%)", rec.workcenter_id.code, rec.distribution)
