from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    credit_app_date = fields.Date(
        related='partner_id.credit_app_date',
        readonly=True,
    )
    credit_warn_msg = fields.Text(
        related='partner_id.credit_warn_msg',
        readonly=True,
    )
    credit_warn_action = fields.Selection(
        selection=[('bypass', 'Bypass'), ('request', 'Request')],
        string='Credit App Action',
    )

    @api.onchange('credit_warn')
    def _onchange_credit_warn(self):
        if self.credit_warn_msg:
            return {'warning': {
                'title': 'Credit Application Warning',
                'message': self.partner_id.credit_warn_msg,
            }}

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            if order.credit_warn_msg:
                if not order.credit_warn_action:
                    raise UserError(_(
                        "%s:\n%s",
                        "Credit Application Warning",
                        order.credit_warn_msg,
                    ))
                if order.credit_warn_action == 'request':
                    # the user has requested a new credit app
                    if (
                        order.partner_id.credit_app_ids
                        and not order.partner_id.credit_app_ids[0:1].received_date
                    ):
                        # a pending credit app already exists
                        order.credit_warn_action = 'bypass'
                    else:
                        self.env['res.partner.credit.app'].create({
                            'partner_id': order.partner_id.id,
                            'order_id': order.id,
                        })
        return res
