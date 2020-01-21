# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, _, fields
from odoo.tools.misc import formatLang, format_date

class report_account_bbc_aged_partner(models.AbstractModel):
    _name = "account.bbc.aged.partner"
    _description = "Aged Partner Balances"
    _inherit = 'account.report'

    filter_date = {'date': '', 'filter': 'today'}
    filter_unfold_all = False
    filter_partner = True

    def _bbc_totals(self, amls, partner_total, all_total):
        # Delinquent Accounts 60+ days (90+ days past invoice date)
        over_60_days = 0.0
        # 20% Rule Cross-aging: If more than 20% of an account is greater than
        # 90 days delinquent, the entire non-delinquent portion of the account
        # must be deducted
        cross_age_20_pct = 0.0
        # Concentration: If a single account represents 20% or more of
        # borrower's A/R, the eligible balance over 20% of all borrower's A/R
        # is ineligible
        over_20_pct = 0.0
        # delinquent credits: credits over 60 days, as a negative number, can
        # be used to increase the borrower's base A/R
        delinquent_cr = 0.0
        # foreign should be calculated without removing portions over 60 days
        foreign = 0.0
        eligible = 0.0
        # bbc_totals = []
        #     0 -- over_60_days
        #     1 -- cross_age_20_pct
        #     2 -- over_20_pct
        #     3 -- delinquent_cr
        #     4 -- foreign
        #     5 -- eligible

        # international customers
        if amls[0]['line'].partner_id.country_id not in [self.env.ref('base.us'), self.env.ref('base.ca'), self.env.ref('base.mx')]:
            # foreign customers are ineligible
            # usa, mexico, and canada are eligible
            partner_bbc_totals = [0.0, 0.0, 0.0, 0.0, partner_total, 0.0]
            bbc_lines = {x['line']: [0.0, 0.0, 0.0, 0.0, x['amount'], 0.0] for x in amls}
            return partner_bbc_totals, bbc_lines
        # period index
        #     6: not due
        #     5: 0 - 30 days
        #     4: 30 - 60 days
        #     3: 60 - 90 days
        #     2: 90 - 120 days
        #     1: older
        for line in amls:
            if line['period'] < 4 and line['amount'] > 0.0:
                over_60_days += line['amount']
        bbc_lines = {}
        for line in amls:
            line_totals = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
            if line['period'] < 4:
                if line['amount'] < 0.0:
                    # delinquent credit
                    delinquent_cr += line['amount']
                    line_totals[3] = line['amount']
                else:
                    # over_60_days
                    line_totals[0] = line['amount']
            elif over_60_days and line['amount'] > 0.0 and over_60_days > 0.2 * partner_total:
                # cross aging rule
                # import pdb
                # pdb.set_trace()
                cross_age_20_pct += line['amount']
                line_totals[1] = line['amount']
            elif line['amount'] > 0.2 * all_total:
                # 20% concentration rule
                over_20_pct += line['amount'] - 0.2 * all_total
                line_totals[2] = line['amount'] - 0.2 * all_total
            line_totals[5] = line['amount'] - sum(line_totals)
            bbc_lines[line['line']] = line_totals
            eligible += line_totals[5]

        partner_bbc_totals = [
            over_60_days,
            cross_age_20_pct,
            over_20_pct,
            delinquent_cr,
            foreign,
            eligible,
        ]
        return partner_bbc_totals, bbc_lines

    def _get_columns_name(self, options):
        columns = [{}]
        columns += [
            {'name': v, 'class': 'number', 'style': 'white-space:nowrap;'}
            for v in [
                _("Invoice Date"),
                _("Not due on %s") % format_date(self.env, options['date']['date']),
                _("0 - 30"),
                _("30 - 60"),
                _("60 - 90"),
                _("90 - 120"),
                _("Older"),
                _("Total"),
                _("Over 60"),
                _("Cross Aged&nbsp;20&#37;"),
                _("20&#37;Conc"),
                _("Delinquent Credit"),
                _("Foreign"),
                _("BBC Eligible"),
            ]
        ]
        return columns

    def _get_templates(self):
        templates = super(report_account_bbc_aged_partner, self)._get_templates()
        templates['main_template'] = 'account_reports.template_aged_partner_balance_report'
        try:
            self.env['ir.ui.view'].get_view_id('account_reports.template_aged_partner_balance_line_report')
            templates['line_template'] = 'account_reports.template_aged_partner_balance_line_report'
        except ValueError:
            pass
        return templates

    def _format(self, value):
        if self.env.context.get('no_format'):
            return value
        currency_id = self.env.user.company_id.currency_id
        if currency_id.is_zero(value):
            # don't print -0.0 in reports
            value = abs(value)
        return formatLang(self.env, value, currency_obj=currency_id)

    @api.model
    def _get_lines(self, options, line_id=None):
        sign = -1.0 if self.env.context.get('aged_balance') else 1.0
        lines = []
        bbc_totals = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        account_types = [self.env.context.get('account_type')]
        results, total, amls = self.env['report.account.report_agedpartnerbalance'].with_context(include_nullified_amount=True)._get_partner_move_lines(account_types, self._context['date_to'], 'posted', 30)
        for values in results:
            if line_id and 'partner_%s' % (values['partner_id'],) != line_id:
                continue
            bbc_partner_totals, bbc_line_totals = self._bbc_totals(amls[values['partner_id']], values['total'],
                                                                   total[5])
            bbc_totals = [a + b for a, b in zip(bbc_totals, bbc_partner_totals)]
            vals = {
                'id': 'partner_%s' % (values['partner_id'],),
                'name': values['name'],
                'level': 2,
                'columns': [{'name': ''}] + [{'name': self.format_value(sign * v)} for v in [values['direction'], values['4'],
                                                                                                 values['3'], values['2'],
                                                                                                 values['1'], values['0'], values['total']]+ bbc_partner_totals],
                'trust': values['trust'],
                'unfoldable': True,
                'unfolded': 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'),
            }
            lines.append(vals)
            if 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'):
                for line in amls[values['partner_id']]:
                    aml = line['line']
                    caret_type = 'account.move'
                    if aml.invoice_id:
                        caret_type = 'account.invoice.in' if aml.invoice_id.type in ('in_refund', 'in_invoice') else 'account.invoice.out'
                    elif aml.payment_id:
                        caret_type = 'account.payment'
                    column = [x and self._format(x) or '' for x in bbc_line_totals[aml]]
                    vals = {
                        'id': aml.id,
                        'name': format_date(self.env, aml.date_maturity or aml.date),
                        'class': 'date',
                        'caret_options': caret_type,
                        'level': 4,
                        'parent_id': 'partner_%s' % (values['partner_id'],),
                        'columns': [{'name': aml.invoice_id.date}] +\
                                   [{'name': v} for v in [line['period'] == 6-i and self.format_value(sign * line['amount']) or '' for i in range(7)]] +\
                                   [{'name': v} for v in column],
                        'action_context': aml.get_action_context(),
                    }
                    lines.append(vals)
        if total and not line_id:
            total_line = {
                'id': 0,
                'name': _('Total'),
                'class': 'total',
                'level': 2,
                'columns': [{'name': ''}] + [{'name': self.format_value(sign * v)} for v in [total[6], total[4], total[3], total[2], total[1], total[0], total[5]] + bbc_totals],
            }
            lines.append(total_line)
        return lines


class report_account_bbc_aged_receivable(models.AbstractModel):
    _name = "account.bbc.aged.receivable"
    _description = "Aged Receivable"
    _inherit = "account.bbc.aged.partner"

    def _set_context(self, options):
        ctx = super(report_account_bbc_aged_receivable, self)._set_context(options)
        ctx['account_type'] = 'receivable'
        return ctx

    def _get_report_name(self):
        return _("BBC Aged Receivable")

    def _get_templates(self):
        templates = super(report_account_bbc_aged_receivable, self)._get_templates()
        templates['line_template'] = 'account_reports.line_template_aged_receivable_report'
        return templates
