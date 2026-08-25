from odoo import models


class OutstandingStatementWizard(models.TransientModel):
    _inherit = 'outstanding.statement.wizard'

    def _prepare_individual_statement(self):
        self.ensure_one()
        statements = []
        for partner in self._context['active_ids']:
            statements.append({
                'date_end': self.date_end,
                'company_id': self.company_id.id,
                'partner_ids': [partner],
                'show_aging_buckets': self.show_aging_buckets,
                'filter_non_due_partners': self.filter_partners_non_due,
                'account_type': self.account_type,
                'aging_type': self.aging_type,
                'filter_negative_balances': self.filter_negative_balances,
                'is_outstanding': True,
            })
        return statements

    def _validate_partner(self, partner):
        is_valid_partner = True
        invalid_company_partner = partner.is_company and  not partner.child_ids.filtered(
                lambda child: child.type == 'invoice' and child.email)
        company_partner = partner.child_ids.filtered(lambda p: p.type == 'invoice' and p.email)
        if invalid_company_partner:
            self.env['account.mail.log'].create(
                {'log_type': 'error',
                 'message': f'Customer {partner.display_name} should have an '
                            f'invoice address with an email'})
            is_valid_partner = False
        invalid_individual_partner = not partner.is_company and not partner.email
        if invalid_individual_partner:
            self.env['account.mail.log'].create(
                {'log_type': 'error',
                 'message': f'Customer {partner.display_name} should have an email'})
            is_valid_partner = False
        valid_partner = self.env['res.partner']
        if company_partner:
            valid_partner = company_partner
        if not partner.is_company and partner.email:
            valid_partner = partner
        return is_valid_partner, valid_partner

    def send_statement_by_email(self):
        statements = self._prepare_individual_statement()
        report_name = 'partner_statement.outstanding_statement'
        template = self.env.ref('azi_account_mail.email_template_outstanding_statement', raise_if_not_found=False)
        outstanding_report = self.env['ir.actions.report'].search(
            [('report_name', '=', report_name), ('report_type', '=', 'qweb-pdf')],
            limit=1)
        for statement in statements:
            partner = self.env["res.partner"].browse(statement['partner_ids'])
            valid_partner, mail_partner = self._validate_partner(partner)
            if valid_partner:
                pdf_content, _ = outstanding_report._render_qweb_pdf(outstanding_report.id, res_ids=[partner.id], data=statement)
                attachment = self.env['ir.attachment'].create({
                    'name': f"Outstanding Statement - {partner.name}.pdf",
                    'type': 'binary',
                    'raw': pdf_content,
                    'res_model': 'res.partner',
                    'res_id': partner.id,
                    'mimetype': 'application/pdf',
                })
                mail_values = template.generate_email(partner.id,
                                                      ['subject', 'body_html', 'email_from', 'email_to', 'partner_to'])

                if isinstance(mail_values, dict):
                    mail_values.update({
                        'attachment_ids': [(4, attachment.id)],
                        'recipient_ids': [(4, mail_partner.id)],
                        'model': 'res.partner',
                        'res_id': partner.id,
                    })
                    mail_values.pop('attachments')
                    mail = self.env['mail.mail'].create(mail_values)

                    mail.send()
                # template.send_mail(
                #     self.id,
                #     force_send=True,
                #     email_values={'recipient_ids': mail_partner, 'attachment_ids': outstanding_report},
                #
                # )
                self.env['account.mail.log'].create(
                    {'log_type': 'info',
                     'message': f'Outstanding email sent to  {partner.display_name}'})
