from odoo import models, api
from odoo.exceptions import ValidationError
from odoo.tools.misc import get_lang


class AccountMove(models.Model):
    _inherit = 'account.move'

    @staticmethod
    def _validate_partners(partners):
        company_partners = partners.filtered(lambda p: p.is_company)
        invalid_company_partners = company_partners.filtered(
            lambda company: not company.child_ids.filtered(
                lambda child: child.type == 'invoice' and child.email
            )
        )
        company_partners = company_partners.mapped('child_ids').filtered(lambda p: p.type == 'invoice' and p.email)
        if invalid_company_partners:
            partner_names = '\n'.join(invalid_company_partners.mapped('display_name'))
            raise ValidationError(
                f"Customers should have an invoice address with an email, please check the following"
                f" customers {partner_names}")
        individual_partners = partners.filtered(lambda p: not p.is_company)
        invalid_individual_partners = individual_partners.filtered(lambda p: not p.email)
        if invalid_individual_partners:
            individual_partner_names = '\n'.join(invalid_individual_partners.mapped('display_name'))
            raise ValidationError(f"Individual Customers should have an email, please check the following "
                                  f"customers {individual_partner_names}")
        return company_partners + individual_partners

    def action_invoice_sent(self):
        report_action = super(AccountMove, self).action_invoice_sent()
        partners = self.mapped('partner_id')
        recipient_partners = self._validate_partners(partners)
        if report_action.get('context') and recipient_partners:
            report_action['context'].update(default_partner_ids=recipient_partners.ids)
        return report_action

    def action_send_and_print(self):
        res = super(AccountMove, self).action_send_and_print()
        partners = self.mapped('partner_id')
        recipient_partners = self._validate_partners(partners)
        if recipient_partners:
            res['context'].update(default_partner_ids=recipient_partners.ids)
        return res

    def send_separate_invoice(self):
        active_ids = self.env.context.get('active_ids', [])
        invoices = self.browse(active_ids)
        partners = invoices.mapped('partner_id')
        self._validate_partners(partners)
        for invoice in invoices:
            partner = invoice.partner_id
            lang = get_lang(self.env, partner.lang).code if partner.lang else self.env.lang
            recipient = invoice._validate_partners(partner)
            template = self.env.ref(invoice._get_mail_template(), raise_if_not_found=False)
            wizard = self.env['mail.compose.message'].with_context(
                active_id=invoice.id,
                active_ids=[invoice.id],
                active_model='account.move',
                default_partner_ids=recipient and recipient.ids or [],
                lang=lang,
            ).create({
                'template_id': template.id,
                'composition_mode': 'comment',
            })
            wizard._onchange_template_id_wrapper()
            _, messages = wizard.with_context(no_new_invoice=True, mailing_document_based=True)._action_send_mail()
            for message in messages:
                message.mapped('mail_ids').send()
