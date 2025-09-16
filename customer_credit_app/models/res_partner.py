from odoo import fields, models, api
from dateutil.relativedelta import relativedelta


class ResPartner(models.Model):
    _inherit = 'res.partner'

    credit_app_ids = fields.One2many(
        comodel_name='res.partner.credit.app',
        inverse_name='partner_id',
        string='Credit App',
    )
    credit_app_date = fields.Date(
        string='Credit App Date',
        compute='_compute_credit_app',
        compute_sudo=True,
        store=True,
    )
    credit_warn = fields.Boolean(
        string='Credit App Warn',
        compute='_compute_credit_app',
        compute_sudo=True,
    )
    credit_warn_msg = fields.Text(
        string='Credit App Warn Msg',
        compute='_compute_credit_app',
        compute_sudo=True,
    )

    @api.depends('credit_app_ids')
    def _compute_credit_app(self):
        validity_months = self.env['ir.config_parameter'].sudo().get_param(
            'customer_credit_app.validity_months')
        expiry_date = fields.Date.today() - relativedelta(months=int(validity_months))
        for rec in self:
            if not rec.industry_id.credit_app:
                rec.credit_app_date = False
                rec.credit_warn = False
                rec.credit_warn_msg = False
                continue
            latest_credit_app = rec.credit_app_ids and rec.credit_app_ids[0] or False
            if not latest_credit_app:
                rec.credit_app_date = False
                rec.credit_warn = True
                rec.credit_warn_msg = "No credit app on file"
            elif not latest_credit_app.received_date:
                latest_complete_app = rec.credit_app_ids.filtered(
                    lambda x: x.received_date)
                rec.credit_app_date = latest_complete_app.received_date
                rec.credit_warn = True
                rec.credit_warn_msg = "Credit app request pending"
            elif latest_credit_app.received_date < expiry_date:
                rec.credit_app_date = latest_credit_app.received_date
                rec.credit_warn = True
                rec.credit_warn_msg = "Credit app expired"
            else:
                rec.credit_app_date = latest_credit_app.received_date
                rec.credit_warn = False
                rec.credit_warn_msg = False
