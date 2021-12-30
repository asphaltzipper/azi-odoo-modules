from odoo import models, fields, api, tools


class LeaveAllocationSummary(models.Model):
    _name = 'leave.allocation.summary'
    _description = 'Leave Allocation Summary'
    _auto = False
    _order = 'year desc, type_id'

    year = fields.Integer("Year")
    employee_id = fields.Many2one('hr.employee', 'Employee')
    type_id = fields.Many2one('leave.type', 'Leave Type')
    lost = fields.Float('Lost')
    rollover = fields.Float('Rollover')
    td_adjust = fields.Float('TD Adjusted')
    td_accrue = fields.Float('TD Accrued')
    td_consume = fields.Float('TD Consumed')
    ye_adjust = fields.Float('YE Adjusted')
    ye_accrue = fields.Float('YE Accrued')
    ye_consume = fields.Float('YE Consumed')
    to_date_balance = fields.Float('TD Balance')
    year_end_balance = fields.Float('YE Balance')
    unit = fields.Selection(related='type_id.leave_unit')

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'leave_allocation_summary')
        self._cr.execute("""
CREATE VIEW leave_allocation_summary AS (
    with full_totals as (
        -- all allocation entries
        select
            employee_id,
            type_id,
            allocation_type as alloc_type,
            date_part('year', start_date) as alloc_year,
            sum(alloc_amount) as alloc_amount
        from leave_allocation
        group by employee_id, type_id, date_part('year', start_date), allocation_type
    ),
    ytd_totals as (
        -- allocation entries thru today
        select
            employee_id,
            type_id,
            allocation_type as alloc_type,
            date_part('year', start_date) as alloc_year,
            sum(alloc_amount) as alloc_amount
        from leave_allocation
        where start_date <= now()
        group by employee_id, type_id, date_part('year', start_date), allocation_type
    )
    select
        ft.employee_id * 10000 + ft.alloc_year * 1000 + ft.type_id as id, 
        ft.alloc_year as "year",
        ft.employee_id,
        ft.type_id,
        sum(coalesce(lo.alloc_amount, 0)) as "lost",
        sum(coalesce(ro.alloc_amount, 0)) as "rollover",
        sum(coalesce(yad.alloc_amount, 0)) as "td_adjust",
        sum(coalesce(yac.alloc_amount, 0)) as "td_accrue",
        sum(coalesce(yco.alloc_amount, 0)) as "td_consume",
        sum(coalesce(fad.alloc_amount, 0)) as "ye_adjust",
        sum(coalesce(fac.alloc_amount, 0)) as "ye_accrue",
        sum(coalesce(fco.alloc_amount, 0)) as "ye_consume",
        sum(coalesce(yt.alloc_amount, 0)) as "to_date_balance",
        sum(coalesce(ft.alloc_amount, 0)) as "year_end_balance"
    from full_totals ft
    left join ytd_totals as yt on yt.employee_id=ft.employee_id and yt.type_id=ft.type_id and yt.alloc_year=ft.alloc_year and yt.alloc_type=ft.alloc_type
    left join full_totals lo on lo.employee_id=ft.employee_id and lo.type_id=ft.type_id and lo.alloc_year=ft.alloc_year and lo.alloc_type=ft.alloc_type and lo.alloc_type='lost'
    left join full_totals ro on ro.employee_id=ft.employee_id and ro.type_id=ft.type_id and ro.alloc_year=ft.alloc_year and ro.alloc_type=ft.alloc_type and ro.alloc_type='rollover'
    left join full_totals fad on fad.employee_id=ft.employee_id and fad.type_id=ft.type_id and fad.alloc_year=ft.alloc_year and fad.alloc_type=ft.alloc_type and fad.alloc_type='adjusted'
    left join ytd_totals yad on yad.employee_id=ft.employee_id and yad.type_id=ft.type_id and yad.alloc_year=ft.alloc_year and yad.alloc_type=ft.alloc_type and yad.alloc_type='adjusted'
    left join full_totals fac on fac.employee_id=ft.employee_id and fac.type_id=ft.type_id and fac.alloc_year=ft.alloc_year and fac.alloc_type=ft.alloc_type and fac.alloc_type='accrued'
    left join ytd_totals yac on yac.employee_id=ft.employee_id and yac.type_id=ft.type_id and yac.alloc_year=ft.alloc_year and yac.alloc_type=ft.alloc_type and yac.alloc_type='accrued'
    left join full_totals fco on fco.employee_id=ft.employee_id and fco.type_id=ft.type_id and fco.alloc_year=ft.alloc_year and fco.alloc_type=ft.alloc_type and fco.alloc_type='consumed'
    left join ytd_totals yco on yco.employee_id=ft.employee_id and yco.type_id=ft.type_id and yco.alloc_year=ft.alloc_year and yco.alloc_type=ft.alloc_type and yco.alloc_type='consumed'
    group by ft.alloc_year, ft.employee_id, ft.type_id
    order by "year", ft.employee_id, ft.type_id
)
        """)
