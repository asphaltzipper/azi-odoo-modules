import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class WizardHrLeaveGenerateAccruals(models.TransientModel):
    _name = 'wizard.leave.generate.accruals'
    _description = "Generate Year Leave Accruals Wizard"

    def get_years(self):
        return [(num, num) for num in range((datetime.date.today().year - 10), (datetime.date.today().year + 2))]

    year = fields.Selection(
        selection=lambda self: self.get_years(),
        string="Year",
        default=datetime.date.today().year,
        required=True,
        help="Specify the year for which to generate accruals.\n"
             "This should only done once at the beginning of the current year."
    )

    leave_type_id = fields.Many2one(
        comodel_name='leave.type',
        string="Leave Type",
        help="Leave blank to process all leave types",
    )

    department_id = fields.Many2one(
        string="Department",
        comodel_name='hr.department',
        help="Leave blank to process all departments",
    )

    employee_id = fields.Many2one(
        string="Employee",
        comodel_name='hr.employee',
        help="Leave blank to process all employees",
    )

    def generate_accruals(self, year):
        start_date = datetime.date(int(self.year), 1, 1)
        end_date = datetime.date(int(self.year), 12, 31)
        previous_year_start_date = datetime.date(int(self.year) - 1, 1, 1)

        # unless leave type specified, get all
        leave_types = self.leave_type_id or self.env['leave.type'].search([])

        # unless employee specified, get all
        if self.employee_id:
            employees = self.employee_id
        else:
            # unless department specified, get all employees
            if self.department_id:
                employees = self.env['hr.employee'].search([('department_id', '=', self.department_id.id)])
            else:
                employees = self.env['hr.employee'].search([])

        # check for existing accruals
        if self.env['leave.allocation'].search_count([
            ('end_date', '>=', start_date),
            ('end_date', '<=', end_date),
            ('allocation_type', 'in', ['accrued', 'rollover', 'lost']),
            ('employee_id', 'in', employees.ids),
            ('type_id', 'in', leave_types.ids),
        ]):
            raise ValidationError("Automatic allocation entries already exist for %s.\n"
                                  "First, delete allocations of type Accrued or Rollover.\n"
                                  "Then, run the wizard again." %
                                  self.year)

        # check for existing lost adjustment
        if self.env['leave.allocation'].search_count([
            ('end_date', '>=', previous_year_start_date),
            ('end_date', '<', start_date),
            ('allocation_type', 'in', ['lost']),
            ('employee_id', 'in', employees.ids),
            ('type_id', 'in', leave_types.ids),
        ]):
            raise ValidationError("Lost adjustment already exists for year transition %s - %s.\n"
                                  "First, delete the Lost allocation.\n"
                                  "Then, run the wizard again." %
                                  (previous_year_start_date.year, self.year))

        # get previous year ending balances
        previous_balances = self.env['leave.allocation'].read_group(
            domain=[
                ('type_id', 'in', leave_types.ids),
                ('employee_id', 'in', employees.ids),
                ('start_date', '>=', previous_year_start_date),
                ('end_date', '<', start_date),
            ],
            fields=['employee_id', 'type_id', 'alloc_amount'],
            groupby=['employee_id', 'type_id'],
            orderby='employee_id, type_id',
            lazy=False,
        )

        # create rollover entries
        leave_alloc = self.env['leave.allocation']
        for balance in previous_balances:
            leave_type = leave_types.filtered(lambda x: x.id == balance['type_id'][0])
            new_balance = balance['alloc_amount']
            if leave_type.limit_rollover and new_balance > leave_type.rollover_limit:
                leave_alloc.create({
                    'employee_id': balance['employee_id'][0],
                    'type_id': leave_type.id,
                    'allocation_type': 'lost',
                    'alloc_amount': leave_type.rollover_limit - balance['alloc_amount'],
                    'start_date': start_date - datetime.timedelta(days=1),
                    'end_date': start_date - datetime.timedelta(days=1),
                })
                new_balance = leave_type.rollover_limit
            if new_balance:
                leave_alloc.create({
                    'employee_id': balance['employee_id'][0],
                    'type_id': leave_type.id,
                    'allocation_type': 'rollover',
                    'alloc_amount': new_balance,
                    'start_date': start_date,
                    'end_date': start_date,
                })

        # generate accrual entries
        assigned_policies = self.env['leave.policy.assign'].search([
            ('employee_id', 'in', employees.ids),
            ('type_id', 'in', leave_types.ids),
            ('start_date', '<=', end_date),
            '|',
            ('end_date', '=', False),
            ('end_date', '>=', start_date),
        ])
        assigned_policies.generate_accruals(int(self.year))
