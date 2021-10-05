from odoo import models, fields, api, tools


class LeaveAccrualAllocated(models.Model):
    _name = 'leave.accrual.allocated'
    _description = 'Leave Accrual allocated'
    _auto = False
    _order = 'type_id'

    type_id = fields.Many2one('leave.type', 'Leave Type')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    opening_balance = fields.Float('Opening Balance')
    adjust = fields.Float('Adjust')
    allocated_amount = fields.Float('Amount')
    used_amount = fields.Float('Used Amount')
    balance = fields.Float('Balance', compute='_compute_balance')
    unit = fields.Selection(related='type_id.leave_unit')

    @api.depends('opening_balance', 'adjust', 'allocated_amount', 'used_amount')
    def _compute_balance(self):
        for record in self:
            record.balance = record.opening_balance - record.adjust + record.allocated_amount - record.used_amount

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'leave_accrual_allocated')
        self._cr.execute("""
            CREATE VIEW leave_accrual_allocated AS (
                select
                    CONCAT(acr.type_id,acr.employee_id)::integer as id,
                    acr.type_id,
                    acr.employee_id,
                    date_trunc('year', now()) as start_date,
                    acr.end_date,
                    alc.alloc_amount as allocated_amount, 
                    alc.used_amount,
                    acr.balance as opening_balance,
                    acr.adjust 
                    from (
                        select
                            lap.type_id,
                            lpa.employee_id,
                            al.policy_assign_id,
                            al.year, 
                            al.balance, 
                            al.adjust,
                            current_date as end_date       
                        from leave_policy_assign as lpa, leave_policy_assign_line as al, leave_accrual_policy as lap 
                        where al.year = extract(year from now()) and al.policy_assign_id = lpa.id and  lap.id=lpa.policy_id
                        group by lap.type_id, lpa.employee_id, al.policy_assign_id, al.year, al.balance, al.adjust
                    ) as acr
                    left join (
                        select
                            employee_id,
                            type_id,
                            sum(case
                            when allocation_type = 'add'  then
                                alloc_amount
                            end) as alloc_amount,
                            sum(case
                            when allocation_type = 'remove'  then
                                used_amount
                            end) as used_amount
                        from leave_allocation
                        where start_date <= now() and start_date >= date_trunc('year', now()) 
                        group by employee_id, type_id
                    ) as alc on alc.employee_id=acr.employee_id and alc.type_id=acr.type_id
            
            )
        """)
