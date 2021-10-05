import datetime
import calendar
from dateutil.relativedelta import relativedelta

from odoo import models


class LeaveAccrualReport(models.AbstractModel):
    _name = 'report.hr_leave_accrual.leave_accrual_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, policy):
        header = workbook.add_format({'bold': True, 'align': 'center'})
        header_date = workbook.add_format({'bold': True, 'align': 'center', 'num_format': 'mm-dd-yyyy'})
        row_date = workbook.add_format({'num_format': 'mm-dd-yyyy'})
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        year = int(data.get('year', 0))
        period_duration = policy.period_duration
        period_unit = policy.period_unit
        if start_date and end_date:
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
            sheet = workbook.add_worksheet(policy.name)
            sheet.set_column(0, 4, 20)
            sheet.write(0, 0, "Employee", header)
            sheet.write(0, 1, "Hire Date", header)
            sheet.write(0, 2, "Years Of Service", header)
            sheet.write(0, 3, policy.rate_unit + " per period", header)
            sheet.merge_range(0, 4, 0, 5, start_date - datetime.timedelta(days=1), header_date)
            sheet.write(1, 4, "Adjust", header)
            sheet.write(1, 5, "Balance", header)
            allocation_used_dates = []
            if period_unit == 'week':
                increment_date = relativedelta(weeks=period_duration)
            elif period_unit == 'half_month':
                increment_date = relativedelta(days=15 * period_duration)
            else:
                increment_date = relativedelta(months=period_duration)
            half_month = period_unit == 'half_month' and period_duration == 1
            i = 6
            while start_date <= end_date:
                if half_month:
                    if start_date.day == 1:
                        end_date_period = datetime.date(start_date.year, start_date.month, 15)
                        sheet.merge_range(0, i, 0, i + 3, end_date_period, header_date)
                        sheet.write(1, i, "Accrued", header)
                        sheet.write(1, i + 1, "Used", header)
                        sheet.write(1, i + 2, "Adjust", header)
                        sheet.write(1, i + 3, "Balance", header)
                        allocation_used_dates.append(end_date_period)
                    if start_date.day == 15:
                        calendar_month = calendar.monthrange(start_date.year, start_date.month)
                        end_date_period = datetime.date(start_date.year, start_date.month, calendar_month[1])
                        sheet.merge_range(0, i, 0, i + 3, end_date_period, header_date)
                        sheet.write(1, i, "Accrued", header)
                        sheet.write(1, i + 1, "Used", header)
                        sheet.write(1, i + 2, "Adjust", header)
                        sheet.write(1, i + 3, "Balance", header)
                        allocation_used_dates.append(end_date_period)
                else:
                    end_date_period = start_date + increment_date
                    sheet.merge_range(0, i, 0, i + 3, end_date_period, header_date)
                    sheet.write(1, i, "Accrued", header)
                    sheet.write(1, i + 1, "Used", header)
                    sheet.write(1, i + 2, "Adjust", header)
                    sheet.write(1, i + 3, "Balance", header)
                    allocation_used_dates.append(end_date_period)

                if half_month:
                    if end_date_period.day == 15:
                        start_date = end_date_period
                    else:
                        end_of_next_month = start_date + relativedelta(months=1)
                        start_date = datetime.date(end_of_next_month.year, end_of_next_month.month, 1)
                else:
                    start_date = end_date_period + datetime.timedelta(days=1)
                i += 4

            count = 2
            for assign in policy.policy_assign_ids:
                line_policy = assign.policy_line_ids.filtered(lambda l: l.year == year)
                if line_policy:
                    hire_date = assign.employee_id.hire_date and datetime.date.strftime(assign.employee_id.hire_date, '%m-%d-%Y') or ""
                    sheet.write(count, 0, assign.employee_id.name, header)
                    sheet.write(count, 1, hire_date, row_date)
                    no_of_years = 0
                    if assign.employee_id.hire_date:
                        no_of_years = relativedelta(datetime.date.today(), assign.employee_id.hire_date)
                        no_of_years = round((no_of_years.years + (no_of_years.months / 12)), 2)

                    sheet.write(count, 2, no_of_years)
                    sheet.write(count, 3, policy.rate)
                    sheet.write(count, 4, line_policy.adjust)
                    sheet.write(count, 5, line_policy.balance)
                    total_balance = line_policy.balance - line_policy.adjust
                    col = 6
                    for allocation in allocation_used_dates:
                        allocated = line_policy.leave_allocation_ids.filtered(lambda l:
                                                                              l.start_date < allocation <= l.end_date)
                        used_allocation = self.env['leave.allocation'].search([
                            ('employee_id', '=', assign.employee_id.id), ('start_date', '>=', allocated.start_date),
                            ('start_date', '<=', allocated.end_date), ('allocation_type', '=', 'remove'),
                            ('type_id', '=', assign.policy_id.type_id.id)])
                        allocated_amount = sum(allocated.mapped('alloc_amount'))
                        used_amount = sum(used_allocation.mapped('used_amount'))
                        total_balance += allocated_amount - used_amount
                        sheet.write(count, col, allocated_amount)
                        sheet.write(count, col + 1, used_amount)
                        sheet.write(count, col + 2, "")
                        sheet.write(count, col + 3, total_balance)
                        col += 4
                    count += 1
