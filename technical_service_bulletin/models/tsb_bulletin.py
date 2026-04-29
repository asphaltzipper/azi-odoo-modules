from odoo import models, fields, api


class TsbBulletin(models.Model):
    _name = 'tsb.bulletin'
    _description = 'Technical Service Bulletin'

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
    )
    is_done = fields.Boolean(
        string='Is Done',
        compute='_compute_is_done',
        store=True,
    )

    @api.depends('serial_ids')
    def _compute_is_done(self):
        for rec in self:
            rec.is_done = rec.serial_ids and all(rec.serial_ids.mapped('done_date')) or False

    @api.depends('serial_ids')
    def _compute_done_date(self):
        for rec in self:
            rec.done_date = rec.serial_ids and max(rec.serial_ids.mapped('done_date')) or False
