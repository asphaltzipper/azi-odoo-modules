from datetime import datetime, timedelta
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT
from odoo import api, fields, models


class TaxReport(models.AbstractModel):
    """Model of Taxes per Month"""

    _name = 'tax.report'

    def _format_date_to_partner_lang(self, str_date, partner_id):
        lang_code = self.env['res.partner'].browse(partner_id).lang
        lang = self.env['res.lang']._lang_get(lang_code)
        date = datetime.strptime(str_date, DEFAULT_SERVER_DATE_FORMAT).date()
        return date.strftime(lang.date_format)

    def _display_lines_sql_q1(self, partners, date_end):
        return """
            select
                s.code as state,
                sp.city,
                sp.zip,
                i.number as invoice_number,
                date_invoice,
                coalesce(pp.name, p.name) as partner_name,
                i.amount_untaxed,
                t.tax_total,
                i.amount_total,
                -- tax,
                -- extended total,
                *
            from account_invoice as i
            left join (
                select
                    invoice_id,
                    sum(amount) as tax_total
                from account_invoice_tax
                group by invoice_id
            ) as t on t.invoice_id=i.id
            left join res_partner as sp on sp.id=i.partner_shipping_id
            left join res_partner as p on p.id=i.partner_id
            left join res_partner as pp on pp.id=p.parent_id
            left join res_country_state as s on s.id=sp.state_id
            where i.type='out_invoice'
            and i.state in ('open', 'paid')
            and coalesce(t.tax_total, 0)>0
            and date_invoice>=%s
            and date_invoice<$s
            order by s.code, p.zip, date_invoice
        """ % (date_start, date_end)

    @api.multi
    def render_html(self, docids, data):
        company_id = data['company_id']
        partner_ids = data['partner_ids']
        date_end = data['date_end']
        today = fields.Date.today()

        buckets_to_display = {}
        lines_to_display, amount_due = {}, {}
        currency_to_display = {}
        today_display, date_end_display = {}, {}

        lines = self._get_account_display_lines(
            company_id, partner_ids, date_end)

        for partner_id in partner_ids:
            lines_to_display[partner_id], amount_due[partner_id] = {}, {}
            currency_to_display[partner_id] = {}
            today_display[partner_id] = self._format_date_to_partner_lang(
                today, partner_id)
            date_end_display[partner_id] = self._format_date_to_partner_lang(
                date_end, partner_id)
            for line in lines[partner_id]:
                currency = self.env['res.currency'].browse(line['currency_id'])
                if currency not in lines_to_display[partner_id]:
                    lines_to_display[partner_id][currency] = []
                    currency_to_display[partner_id][currency] = currency
                    amount_due[partner_id][currency] = 0.0
                if not line['blocked']:
                    amount_due[partner_id][currency] += line['open_amount']
                line['balance'] = amount_due[partner_id][currency]
                line['date'] = self._format_date_to_partner_lang(
                    line['date'], partner_id)
                line['date_maturity'] = self._format_date_to_partner_lang(
                    line['date_maturity'], partner_id)
                lines_to_display[partner_id][currency].append(line)

        if data['show_aging_buckets']:
            buckets = self._get_account_show_buckets(
                company_id, partner_ids, date_end)
            for partner_id in partner_ids:
                buckets_to_display[partner_id] = {}
                for line in buckets[partner_id]:
                    currency = self.env['res.currency'].browse(
                        line['currency_id'])
                    if currency not in buckets_to_display[partner_id]:
                        buckets_to_display[partner_id][currency] = []
                    buckets_to_display[partner_id][currency] = line

        docargs = {
            'doc_ids': partner_ids,
            'doc_model': 'res.partner',
            'docs': self.env['res.partner'].browse(partner_ids),
            'Amount_Due': amount_due,
            'Lines': lines_to_display,
            'Buckets': buckets_to_display,
            'Currencies': currency_to_display,
            'Show_Buckets': data['show_aging_buckets'],
            'Filter_non_due_partners': data['filter_non_due_partners'],
            'Date_end': date_end_display,
            'Date': today_display,
        }
        return self.env['report'].render(
            'customer_outstanding_statement.statement', values=docargs)
