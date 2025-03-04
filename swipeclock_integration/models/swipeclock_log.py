from odoo import models, fields, api


class SwipeclockLog(models.Model):
    _name = "swipeclock.log"
    _description = "Swipeclock import log"
    _order = "create_date"

    account_id = fields.Many2one(
        comodel_name='swipeclock.account',
        required=True,
        readonly=True,
    )
    success = fields.Boolean(
        string="Success",
        required=True,
        default=False,
        readonly=True,
    )
    begin_date = fields.Date(
        string="Beginning Date",
        readonly=True,
    )
    employee_count = fields.Integer(
        string="Employee Count",
        readonly=True,
    )
    punch_count = fields.Integer(
        string="Punch Count",
        readonly=True,
    )
    message = fields.Char(
        string="Message",
        readonly=True,
    )
    details = fields.Text(
        string="Details",
        readonly=True,
    )

    def log_entry(self, vals):
        new_cr = self.pool.cursor()
        self.with_env(self.env(cr=new_cr)).create(vals)
        new_cr.commit()
        new_cr.close()

