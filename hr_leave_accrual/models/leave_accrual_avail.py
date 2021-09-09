from odoo import models, fields, api, tools


class LeaveAccrualAvail(models.Model):
    _name = 'leave.accrual.avail'
    _description = 'Leave Accrual Availability'
    _auto = False
    _order = 'employee_id, type_id'

    type_id = fields.Many2one(
        comodel_name='leave.type',
        string="Leave Type",
    )

    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string="Employee",
    )

    amount = fields.Float(
        string="Amount"
    )

    unit = fields.Selection(
        related='type_id.leave_unit',
    )

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'leave_accrual_avail')
        self._cr.execute("""
            CREATE VIEW leave_accrual_avail AS (
                select
                    ((acr.employee_id::bit << 12) | acr.type_id::bit)::integer as id,
                    acr.type_id,
                    acr.employee_id,
                    acr.start_date,
                    acr.end_date,
                    acr.accrue_amount - alc.alloc_amount as amount
                from (
                    -- accrued
                    select
                        lap.type_id,
                        lpa.employee_id,
                        min(lpa.start_date) as start_date,
                        max(coalesce(lpa.end_date, current_date)) as end_date,
                        sum(FLOOR(lap.rate * (
                            case
                            when lap.period_unit='week' then
                                EXTRACT(day FROM age(coalesce(lpa.end_date, current_date), lpa.start_date))/7
                            when lap.period_unit='half_month' then
                                EXTRACT(year FROM age(coalesce(lpa.end_date, current_date), lpa.start_date))*24 +
                                EXTRACT(month FROM age(coalesce(lpa.end_date, current_date), lpa.start_date))*2 +
                                EXTRACT(day FROM age(coalesce(lpa.end_date, current_date), lpa.start_date))/15
                            when lap.period_unit='month' then
                                EXTRACT(year FROM age(coalesce(lpa.end_date, current_date), lpa.start_date))*12 +
                                EXTRACT(month FROM age(coalesce(lpa.end_date, current_date), lpa.start_date))/lap.period_duration
                        end))) as accrue_amount
                    from leave_policy_assign as lpa
                    left join leave_accrual_policy as lap on lap.id=lpa.policy_id
                    group by lap.type_id, lpa.employee_id
                ) as acr
                left join (
                    -- allocated
                    select
                        employee_id,
                        type_id,
                        sum(alloc_amount) as alloc_amount
                    from leave_allocation
                    group by employee_id, type_id
                ) as alc on alc.employee_id=acr.employee_id and alc.type_id=acr.type_id
            )
        """)
