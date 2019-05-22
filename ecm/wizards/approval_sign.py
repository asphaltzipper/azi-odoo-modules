# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class EcmApprovalSign(models.TransientModel):
    _name = 'ecm.eco.approval.sign'
    _description = 'Sign ECO Approval'

    approval_id = fields.Many2one(
        comodel_name='ecm.eco.approval',
        string='Name',
        readonly=True)

    stage_id = fields.Many2one(
        comodel_name='ecm.eco.stage',
        related='approval_id.stage_id',
        required=True,
        readonly=True)

    approval_type = fields.Selection(
        related='approval_id.approval_type',
        string='Type',
        required=True,
        readonly=True)

    state = fields.Selection(
        selection=[('none', 'Pending'),
                   ('approved', 'Approved'),
                   ('rejected', 'Rejected')],
        string="Status",
        default='approved',
        required=True)

    signed_user_id = fields.Many2one(
        comodel_name='res.users',
        string='User',
        required=True,
        default=lambda self: self.env.user)

    signed_date = fields.Date(
        string='Date',
        default=fields.Date.today(),
        required=True)

    @api.multi
    def button_execute(self):
        self.ensure_one()
        self.approval_id.state = self.state
        if self.state == 'none':
            self.approval_id.signed_user_id = False
            self.approval_id.signed_date = False
        else:
            self.approval_id.signed_user_id = self.signed_user_id
            self.approval_id.signed_date = self.signed_date
        return {}
