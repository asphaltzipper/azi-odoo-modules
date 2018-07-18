# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, _, fields
from odoo.tools.misc import formatLang


class report_account_bbc_aged_partner(models.AbstractModel):
    _name = "account.bbc.aged.partner"
    _description = "BBC Aged Partner Balances"

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

    def _format(self, value):
        if self.env.context.get('no_format'):
            return value
        currency_id = self.env.user.company_id.currency_id
        if currency_id.is_zero(value):
            # don't print -0.0 in reports
            value = abs(value)
        return formatLang(self.env, value, currency_obj=currency_id)

    @api.model
    def _lines(self, context, line_id=None):
        sign = -1.0 if self.env.context.get('aged_balance') else 1.0
        lines = []
        bbc_totals = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        results, total, amls = self.env['report.account.report_agedpartnerbalance']._get_partner_move_lines([self._context['account_type']], self._context['date_to'], 'posted', 30)
        for values in results:
            if line_id and values['partner_id'] != line_id:
                continue
            bbc_partner_totals, bbc_line_totals = self._bbc_totals(amls[values['partner_id']], values['total'], total[5])
            bbc_totals = [a + b for a, b in zip(bbc_totals, bbc_partner_totals)]
            vals = {
                'id': values['partner_id'] and values['partner_id'] or -1,
                'name': values['name'],
                'level': 0 if values['partner_id'] else 2,
                'type': values['partner_id'] and 'partner_id' or 'line',
                'footnotes': context._get_footnotes('partner_id', values['partner_id']),
                'columns': [values['direction'], values['4'], values['3'], values['2'], values['1'], values['0'], values['total']] + bbc_partner_totals,
                'trust': values['trust'],
                'unfoldable': values['partner_id'] and True or False,
                'unfolded': values['partner_id'] and (values['partner_id'] in context.unfolded_partners.ids) or False,
                # 'unfolded': True,
            }
            vals['columns'] = [self._format(sign * t) for t in vals['columns']]
            vals['columns'] = [''] + vals['columns']
            lines.append(vals)
            if values['partner_id'] in context.unfolded_partners.ids:
                for line in amls[values['partner_id']]:
                    aml = line['line']
                    columns = [aml.date]
                    columns += [line['period'] == 6-i and self._format(sign * line['amount']) or '' for i in range(7)]
                    columns += [x and self._format(x) or '' for x in bbc_line_totals[aml]]
                    vals = {
                        'id': aml.id,
                        'name': aml.move_id.name if aml.move_id.name else '/',
                        'move_id': aml.move_id.id,
                        'action': aml.get_model_id_and_name(),
                        'level': 1,
                        'type': 'move_line_id',
                        'footnotes': context._get_footnotes('move_line_id', aml.id),
                        'columns': columns,
                    }
                    lines.append(vals)
                vals = {
                    'id': values['partner_id'],
                    'type': 'o_account_reports_domain_total',
                    'name': _('Total '),
                    'footnotes': self.env.context['context_id']._get_footnotes('o_account_reports_domain_total', values['partner_id']),
                    'columns': [values['direction'], values['4'], values['3'], values['2'], values['1'], values['0'], values['total']] + bbc_partner_totals,
                    'level': 1,
                }
                vals['columns'] = [self._format(sign * t) for t in vals['columns']]
                vals['columns'] = [''] + vals['columns']
                lines.append(vals)
        if total and not line_id:
            total_line = {
                'id': 0,
                'name': _('Total'),
                'level': 0,
                'type': 'o_account_reports_domain_total',
                'footnotes': context._get_footnotes('o_account_reports_domain_total', 0),
                'columns': [total[6], total[4], total[3], total[2], total[1], total[0], total[5]] + bbc_totals,
            }
            total_line['columns'] = [self._format(sign * t) for t in total_line['columns']]
            total_line['columns'] = [''] + total_line['columns']
            lines.append(total_line)
        return lines


class report_account_bbc_aged_receivable(models.AbstractModel):
    _name = "account.bbc.aged.receivable"
    _description = "BBC Aged Receivable"
    _inherit = "account.bbc.aged.partner"

    @api.model
    def get_lines(self, context_id, line_id=None):
        if type(context_id) == int:
            context_id = self.env['account.context.bbc.aged.receivable'].search([['id', '=', context_id]])
        new_context = dict(self.env.context)
        new_context.update({
            'date_to': context_id.date_to,
            'context_id': context_id,
            'company_ids': context_id.company_ids.ids,
            'account_type': 'receivable',
        })
        return self.with_context(new_context)._lines(context_id, line_id)

    @api.model
    def get_title(self):
        return _("BBC Aged Receivable")

    @api.model
    def get_name(self):
        return 'bbc_aged_receivable'

    @api.model
    def get_report_type(self):
        return self.env.ref('account_reports.account_report_type_nothing')

    def get_template(self):
        return 'account_reports.report_financial'


class account_context_bbc_aged_receivable(models.TransientModel):
    _name = "account.context.bbc.aged.receivable"
    _description = "A particular context for the BBC aged receivable"
    _inherit = "account.report.context.common"

    fold_field = 'unfolded_partners'
    unfolded_partners = fields.Many2many('res.partner', 'bbc_aged_receivable_context_to_partner', string='Unfolded lines')

    def get_report_obj(self):
        return self.env['account.bbc.aged.receivable']

    def get_columns_names(self):
        return [
            _("Invoice&nbsp;Date"),
            _("Not&nbsp;due&nbsp;on&nbsp;&nbsp; %s") % self.date_to,
            _("0&nbsp;-&nbsp;30"),
            _("30&nbsp;-&nbsp;60"),
            _("60&nbsp;-&nbsp;90"),
            _("90&nbsp;-&nbsp;120"),
            _("Older"),
            _("Total"),
            _("Over&nbsp;60"),
            _("Cross Aged&nbsp;20&#37;"),
            _("20&#37;&nbsp;Conc"),
            _("Delinquent Credit"),
            _("Foreign"),
            _("BBC Eligible"),
        ]

    @api.multi
    def get_columns_types(self):
        return ["date", "number", "number", "number", "number", "number", "number", "number", "number", "number", "number", "number", "number", "number", "number"]


class AccountReportContextCommon(models.TransientModel):
    _inherit = "account.report.context.common"

    def _report_name_to_report_model(self):
        res = super(AccountReportContextCommon, self)._report_name_to_report_model()
        res['bbc_aged_receivable'] = 'account.bbc.aged.receivable'
        return res

    def _report_model_to_report_context(self):
        res = super(AccountReportContextCommon, self)._report_model_to_report_context()
        res['account.bbc.aged.receivable'] = 'account.context.bbc.aged.receivable'
        return res
