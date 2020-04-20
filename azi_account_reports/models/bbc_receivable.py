# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from dateutil.relativedelta import relativedelta

from odoo import models, api, _, fields
from odoo.tools.misc import formatLang, format_date
from odoo.tools import float_is_zero


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

    def _get_partner_move_lines(self, account_type, date_from, target_move, period_length):
        # This method can receive the context key 'include_nullified_amount' {Boolean}
        # Do an invoice and a payment and unreconcile. The amount will be nullified
        # By default, the partner wouldn't appear in this report.
        # The context key allow it to appear
        # In case of a period_length of 30 days as of 2019-02-08, we want the following periods:
        # Name       Stop         Start
        # 1 - 30   : 2019-02-07 - 2019-01-09
        # 31 - 60  : 2019-01-08 - 2018-12-10
        # 61 - 90  : 2018-12-09 - 2018-11-10
        # 91 - 120 : 2018-11-09 - 2018-10-11
        # +120     : 2018-10-10
        ctx = self._context
        periods = {}
        date_from = fields.Date.from_string(date_from)
        start = date_from
        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length)
            period_name = str((5-(i+1)) * period_length + 1) + '-' + str((5-i) * period_length)
            period_stop = (start - relativedelta(days=1)).strftime('%Y-%m-%d')
            if i == 0:
                period_name = '+' + str(4 * period_length)
            periods[str(i)] = {
                'name': period_name,
                'stop': period_stop,
                'start': (i!=0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop

        res = []
        total = []
        partner_clause = ''
        cr = self.env.cr
        user_company = self.env.user.company_id
        user_currency = user_company.currency_id
        company_ids = self._context.get('company_ids') or [user_company.id]
        move_state = ['draft', 'posted']
        if target_move == 'posted':
            move_state = ['posted']
        arg_list = (tuple(move_state), tuple(account_type), date_from, date_from,)
        if ctx.get('partner_ids'):
            partner_clause = 'AND (l.partner_id IN %s)'
            arg_list += (tuple(ctx['partner_ids'].ids),)
        if ctx.get('partner_categories'):
            partner_clause += 'AND (l.partner_id IN %s)'
            partner_ids = self.env['res.partner'].search([('category_id', 'in', ctx['partner_categories'].ids)]).ids
            arg_list += (tuple(partner_ids or [0]),)
        arg_list += (date_from, tuple(company_ids))
        query = '''
            SELECT DISTINCT l.partner_id, UPPER(res_partner.name)
            FROM account_move_line AS l left join res_partner on l.partner_id = res_partner.id, account_account, account_move am
            WHERE (l.account_id = account_account.id)
                AND (l.move_id = am.id)
                AND (am.state IN %s)
                AND (account_account.internal_type IN %s)
                AND (
                        l.reconciled IS FALSE
                        OR l.id IN(
                            SELECT credit_move_id FROM account_partial_reconcile where max_date > %s
                            UNION ALL
                            SELECT debit_move_id FROM account_partial_reconcile where max_date > %s
                        )
                    )
                    ''' + partner_clause + '''
                AND (l.date <= %s)
                AND l.company_id IN %s
            ORDER BY UPPER(res_partner.name)'''
        cr.execute(query, arg_list)

        partners = cr.dictfetchall()
        # put a total of 0
        for i in range(7):
            total.append(0)

        # Build a string like (1,2,3) for easy use in SQL query
        partner_ids = [partner['partner_id'] for partner in partners if partner['partner_id']]
        lines = dict((partner['partner_id'] or False, []) for partner in partners)
        if not partner_ids:
            return [], [], {}

        # Use one query per period and store results in history (a list variable)
        # Each history will contain: history[1] = {'<partner_id>': <partner_debit-credit>}
        history = []
        for i in range(5):
            args_list = (tuple(move_state), tuple(account_type), tuple(partner_ids),)
            dates_query = '(COALESCE(l.date,l.date_maturity)'

            if periods[str(i)]['start'] and periods[str(i)]['stop']:
                dates_query += ' BETWEEN %s AND %s)'
                args_list += (periods[str(i)]['start'], periods[str(i)]['stop'])
            elif periods[str(i)]['start']:
                dates_query += ' >= %s)'
                args_list += (periods[str(i)]['start'],)
            else:
                dates_query += ' <= %s)'
                args_list += (periods[str(i)]['stop'],)
            args_list += (date_from, tuple(company_ids))

            query = '''SELECT l.id
                    FROM account_move_line AS l, account_account, account_move am
                    WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                        AND (am.state IN %s)
                        AND (account_account.internal_type IN %s)
                        AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                        AND ''' + dates_query + '''
                    AND (l.date <= %s)
                    AND l.company_id IN %s
                    ORDER BY COALESCE(l.date, l.date_maturity)'''
            cr.execute(query, args_list)
            partners_amount = {}
            aml_ids = cr.fetchall()
            aml_ids = aml_ids and [x[0] for x in aml_ids] or []
            for line in self.env['account.move.line'].browse(aml_ids).with_context(prefetch_fields=False):
                partner_id = line.partner_id.id or False
                if partner_id not in partners_amount:
                    partners_amount[partner_id] = 0.0
                line_amount = line.company_id.currency_id._convert(line.balance, user_currency, user_company, date_from)
                if user_currency.is_zero(line_amount):
                    continue
                for partial_line in line.matched_debit_ids:
                    if partial_line.max_date <= date_from:
                        line_amount += partial_line.company_id.currency_id._convert(partial_line.amount, user_currency, user_company, date_from)
                for partial_line in line.matched_credit_ids:
                    if partial_line.max_date <= date_from:
                        line_amount -= partial_line.company_id.currency_id._convert(partial_line.amount, user_currency, user_company, date_from)

                if not self.env.user.company_id.currency_id.is_zero(line_amount):
                    partners_amount[partner_id] += line_amount
                    lines.setdefault(partner_id, [])
                    lines[partner_id].append({
                        'line': line,
                        'amount': line_amount,
                        'period': i + 1,
                        })
            history.append(partners_amount)

        # This dictionary will store the not due amount of all partners
        undue_amounts = {}
        query = '''SELECT l.id
                FROM account_move_line AS l, account_account, account_move am
                WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                    AND (am.state IN %s)
                    AND (account_account.internal_type IN %s)
                    AND (COALESCE(l.date,l.date_maturity) >= %s)\
                    AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                AND (l.date <= %s)
                AND l.company_id IN %s
                ORDER BY COALESCE(l.date, l.date_maturity)'''
        cr.execute(query, (tuple(move_state), tuple(account_type), date_from, tuple(partner_ids), date_from, tuple(company_ids)))
        aml_ids = cr.fetchall()
        aml_ids = aml_ids and [x[0] for x in aml_ids] or []
        for line in self.env['account.move.line'].browse(aml_ids):
            partner_id = line.partner_id.id or False
            if partner_id not in undue_amounts:
                undue_amounts[partner_id] = 0.0
            line_amount = line.company_id.currency_id._convert(line.balance, user_currency, user_company, date_from)
            if user_currency.is_zero(line_amount):
                continue
            for partial_line in line.matched_debit_ids:
                if partial_line.max_date <= date_from:
                    line_amount += partial_line.company_id.currency_id._convert(partial_line.amount, user_currency, user_company, date_from)
            for partial_line in line.matched_credit_ids:
                if partial_line.max_date <= date_from:
                    line_amount -= partial_line.company_id.currency_id._convert(partial_line.amount, user_currency, user_company, date_from)
            if not self.env.user.company_id.currency_id.is_zero(line_amount):
                undue_amounts[partner_id] += line_amount
                lines.setdefault(partner_id, [])
                lines[partner_id].append({
                    'line': line,
                    'amount': line_amount,
                    'period': 6,
                })

        for partner in partners:
            if partner['partner_id'] is None:
                partner['partner_id'] = False
            at_least_one_amount = False
            values = {}
            undue_amt = 0.0
            if partner['partner_id'] in undue_amounts:  # Making sure this partner actually was found by the query
                undue_amt = undue_amounts[partner['partner_id']]

            total[6] = total[6] + undue_amt
            values['direction'] = undue_amt
            if not float_is_zero(values['direction'], precision_rounding=self.env.user.company_id.currency_id.rounding):
                at_least_one_amount = True

            for i in range(5):
                during = False
                if partner['partner_id'] in history[i]:
                    during = [history[i][partner['partner_id']]]
                # Adding counter
                total[(i)] = total[(i)] + (during and during[0] or 0)
                values[str(i)] = during and during[0] or 0.0
                if not float_is_zero(values[str(i)], precision_rounding=self.env.user.company_id.currency_id.rounding):
                    at_least_one_amount = True
            values['total'] = sum([values['direction']] + [values[str(i)] for i in range(5)])
            ## Add for total
            total[(i + 1)] += values['total']
            values['partner_id'] = partner['partner_id']
            if partner['partner_id']:
                #browse the partner name and trust field in sudo, as we may not have full access to the record (but we still have to see it in the report)
                browsed_partner = self.env['res.partner'].sudo().browse(partner['partner_id'])
                values['name'] = browsed_partner.name and len(browsed_partner.name) >= 45 and browsed_partner.name[0:40] + '...' or browsed_partner.name
                values['trust'] = browsed_partner.trust
            else:
                values['name'] = _('Unknown Partner')
                values['trust'] = False

            if at_least_one_amount or (self._context.get('include_nullified_amount') and lines[partner['partner_id']]):
                res.append(values)

        return res, total, lines

    @api.model
    def _get_lines(self, options, line_id=None):
        sign = -1.0 if self.env.context.get('aged_balance') else 1.0
        lines = []
        bbc_totals = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        account_types = [self.env.context.get('account_type')]
        results, total, amls = self.with_context(include_nullified_amount=True)._get_partner_move_lines(account_types, self._context['date_to'], 'posted', 30)
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
                'columns': [{'name': ''}] + [{'name': self.format_value(sign * v)} for v in [values['4'],
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
                        'name': format_date(self.env, aml.date or aml.date_maturity),
                        'class': 'date',
                        'caret_options': caret_type,
                        'level': 4,
                        'parent_id': 'partner_%s' % (values['partner_id'],),
                        'columns': [{'name': aml.invoice_id.date}] +\
                                   [{'name': v} for v in [line['period'] == 6-i and self.format_value(sign * line['amount']) or '' for i in range(7) if i !=0]] +\
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
                'columns': [{'name': ''}] + [{'name': self.format_value(sign * v)} for v in [total[4], total[3], total[2], total[1], total[0], total[5]] + bbc_totals],
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
