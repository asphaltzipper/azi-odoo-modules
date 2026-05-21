from odoo import models, fields, api


class TsbBulletin(models.Model):
    _name = 'tsb.bulletin'
    _description = 'Technical Service Bulletin'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Name',
        required=True,
    )
    description = fields.Text(
        string='Description',
        required=True,
    )
    serial_ids = fields.One2many(
        comodel_name='tsb.serial',
        inverse_name='bulletin_id',
    )
    start_date = fields.Date(
        string='Start Date',
        required=True,
        default=fields.Date.today(),
    )
    done_date = fields.Date(
        string='Done Date',
        compute='_compute_done_date',
        compute_sudo = True,
    )
    is_done = fields.Boolean(
        string='Is Done',
        compute='_compute_done_date',
        compute_sudo = True,
        store=True,
    )

    @api.depends('serial_ids')
    def _compute_done_date(self):
        for rec in self:
            done_dates = rec.serial_ids and rec.serial_ids.mapped('done_date') or []
            rec.is_done = done_dates and all(done_dates) or False
            rec.done_date = rec.is_done and max(done_dates) or False
