from odoo import api, fields, models, tools


class MrpAttendanceCompare(models.Model):
    _name = "mrp.attendance.compare"
    _description = "Compare workorder time with employee attendance"
    _auto = False

    # fields selected from the database view
    # te.attendance_id,
    # te.productivity_id,
    # te.time_type,
    # te.employee_id,
    # he.department_id,
    # he.job_id,
    # te.
    # "date",
    # te.punch_hours,
    # te.work_hours,
    # te.workcenter_id,
    # te.workorder_id,
    # mw.production_id,
    # mw.product_id

    user_id = fields.Many2one(
        comodel_name="res.users",
        string="User",
    )
    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Employee",
    )
    workcenter_id = fields.Many2one(
        comodel_name="mrp.workcenter",
        string="Operation",
    )
    entry_date = fields.Date(
        string="Date",
    )
    punch_hours = fields.Float(
        string="Punch Hours",
    )
    work_hours = fields.Float(
        string="Work Hours",
    )
    effectiveness = fields.Float(
        string="Effectiveness",
    )
    department_id = fields.Many2one(
        comodel_name="hr.department",
        string="Department",
    )
    job_id = fields.Many2one(
        comodel_name="hr.job",
        string="Job",
    )

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if (
            'effectiveness' not in fields
            or 'punch_hours' not in fields
            or 'work_hours' not in fields
        ):
            return super(MrpAttendanceCompare, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        res = super(MrpAttendanceCompare, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        for group in res:
            if group['punch_hours']:
                group['effectiveness'] = group['work_hours']/group['punch_hours']
        return res

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'mrp_attendance_compare')
        sql = """
CREATE VIEW mrp_attendance_compare AS (
    -- combined work/punch time data
    select
        row_number() over (order by
            t.user_id,
            t.employee_id,
            t.workcenter_id,
            t.entry_date
        ) as id,
        t.*,
        he.department_id,
        he.job_id
    from (
            select
                he.user_id,
                ha.employee_id,
                ewdl.workcenter_id,
                ha.check_in::date as entry_date,
                sum(ha.worked_hours*ewdl.distribution/100) as punch_hours,
                0 as work_hours,
                0 as effectiveness
            from hr_attendance ha
            left join employee_workcenter_distribution ewd
                on ewd.employee_id=ha.employee_id
                and ewd.start_date<=ha.check_in
                and coalesce(ewd.end_date, '9999-01-01')>=ha.check_in
            left join employee_workcenter_distribution_line ewdl on ewdl.ewd_id=ewd.id
            left join hr_employee he on he.id=ha.employee_id
            where ewdl.workcenter_id is not null
            group by he.user_id, ha.employee_id, ewdl.workcenter_id, ha.check_in::date
        union
            select
                mwp.user_id,
                he.id as employee_id,
                mwp.workcenter_id,
                mwp.date_end::date as entry_date,
                0 as punch_hours,
                sum(mwp.duration/60) as work_hours,
                0 as effectiveness
            from mrp_workcenter_productivity mwp
            left join hr_employee he on he.user_id=mwp.user_id
            group by mwp.user_id, he.id, mwp.workcenter_id, mwp.date_end::date
    ) as t
    left join hr_employee he on he.id=t.employee_id
)
        """
        self.env.cr.execute(sql, {'avg_len': 10})
