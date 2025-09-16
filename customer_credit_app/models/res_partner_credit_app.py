from odoo import fields, models


class PartnerCreditApp(models.Model):
    _name = 'res.partner.credit.app'
    _inherit = ['mail.thread']
    _rec_name = 'partner_id'
    _description = 'Credit Application'
    _order = 'requested_date desc'

    requested_date = fields.Date(
        string='Requested Date',
        required=True,
        default=fields.Date.today,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        required=True,
    )
    order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sales Order',
    )
    received_date = fields.Date(
        string='Received Date',
    )

    def action_open_credit_app(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            'customer_credit_app.res_partner_credit_action_one')
        action['res_id'] = self.id
        return action
