from odoo import models, fields, api, exceptions, _


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    import_date = fields.Datetime(
        string="Import Date",
        readonly=True,
    )
    break_seconds = fields.Integer(
        string="Break Seconds",
        default=0.0,
    )

    @api.depends('check_in', 'check_out', 'break_seconds')
    def _compute_worked_hours(self):
        super(HrAttendance, self)._compute_worked_hours()
        for attendance in self:
            if attendance.worked_hours and attendance.break_seconds:
                attendance.worked_hours -= attendance.break_seconds / 3600.0
