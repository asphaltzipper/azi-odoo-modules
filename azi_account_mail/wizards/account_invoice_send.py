from odoo import models, api, _


class AccountInvoiceSend(models.TransientModel):
    _inherit = 'account.invoice.send'

    @api.onchange('is_email')
    def onchange_is_email(self):
        if self.is_email:
            res_ids = self._context.get('active_ids')
            if not self.composer_id:
                self.composer_id = self.env['mail.compose.message'].create({
                    'composition_mode': 'comment' if len(res_ids) == 1 else 'mass_mail',
                    'template_id': self.template_id.id
                })
            else:
                self.composer_id.composition_mode = 'comment' if len(res_ids) == 1 else 'mass_mail'
                self.composer_id.template_id = self.template_id.id
                self._compute_composition_mode()

            invoices = self.env['account.move'].browse(res_ids)
            partners = invoices.mapped('partner_id')
            recipient_partners = self.env['account.move']._validate_partners(partners)
            ctx = self.env.context.copy()
            if recipient_partners:
                ctx.update(default_partner_ids=recipient_partners.ids)
            self = self.with_context(ctx)
            self.composer_id._onchange_template_id_wrapper()

    @api.onchange('is_email')
    def _compute_invoice_without_email(self):
        for wizard in self:
            if wizard.is_email and len(wizard.invoice_ids) > 1:
                invoices = self.env['account.move'].search([
                    ('id', 'in', self.env.context.get('active_ids'))
                ])
                individual_partner_invoices = invoices.filtered(
                    lambda i: not i.partner_id.is_company and not i.partner_id.email
                )
                company_partner_invoices = invoices.filtered(lambda i: i.partner_id.is_company).filtered(
                    lambda invoice: not invoice.partner_id.child_ids.filtered(
                        lambda child: child.type == 'invoice' and child.email)
                )

                invoices = individual_partner_invoices + company_partner_invoices
                if invoices:
                    wizard.invoice_without_email = "%s\n%s" % (
                        _("The following invoice(s) will not be sent by email, because the customers don't have email address."),
                        "\n".join([i.name for i in invoices])
                    )
                else:
                    wizard.invoice_without_email = False
            else:
                wizard.invoice_without_email = False
