# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import models, api, _, fields
from odoo.tools.misc import formatLang, format_date
from odoo.tools import float_is_zero
from itertools import chain


class report_account_bbc_aged_partner(models.AbstractModel):
    _name = 'account.bbc.aged.partner'
    _description = 'Aged Partner Balances'
    _inherit = 'account.report.custom.handler'

    def _report_custom_engine_bbc_aged_receivable(self, expressions, options, date_scope, current_groupby, next_groupby, offset=0, limit=None):
        return self._aged_partner_report_custom_engine_common_bbc(options, 'asset_receivable', current_groupby, next_groupby, offset=offset, limit=limit)

    def get_total_for_bbc(self, period_table, currency_table, date_end, date_start):
        query = f"""
            WITH period_table(date_start, date_stop, period_index) AS ({period_table})
            SELECT SUM(account_move_line.amount_currency) AS amount_currency            
            FROM "account_move_line" 
            LEFT JOIN "account_account" AS "account_move_line__account_id" 
            ON ("account_move_line"."account_id" = "account_move_line__account_id"."id")
            JOIN {currency_table} ON currency_table.company_id = account_move_line.company_id
             JOIN period_table ON
                (
                    period_table.date_start IS NULL
                    OR COALESCE(account_move_line.date_maturity, account_move_line.date) <= DATE(period_table.date_start)
                )
                AND
                (
                    period_table.date_stop IS NULL
                    OR COALESCE(account_move_line.date_maturity, account_move_line.date) >= DATE(period_table.date_stop)
                )

            WHERE (((((((("account_move_line"."display_type" not in ('line_section', 'line_note')) 
            OR "account_move_line"."display_type" IS NULL) AND (("account_move_line"."parent_state" != 'cancel') 
            OR "account_move_line"."parent_state" IS NULL)) AND ("account_move_line"."company_id" = %s )) 
            AND ("account_move_line"."date" <= %s)) AND ("account_move_line"."date" >= %s)) 
            AND ("account_move_line"."parent_state" = 'posted')) 
            AND ("account_move_line__account_id"."account_type" = 'asset_receivable')) 
            AND ("account_move_line"."company_id" IS NULL  OR ("account_move_line"."company_id" = %s))
            """
        params = [self.env.company.id, date_end, date_start, self.env.company.id]
        self._cr.execute(query, params)
        all_total_line = self._cr.dictfetchall()
        return all_total_line

    def _aged_partner_report_custom_engine_common_bbc(self, options, internal_type, current_groupby, next_groupby, offset=0, limit=None):
        report = self.env['account.report'].browse(options['report_id'])
        report._check_groupby_fields((next_groupby.split(',') if next_groupby else []) + ([current_groupby] if current_groupby else []))

        def minus_days(date_obj, days):
            return fields.Date.to_string(date_obj - relativedelta(days=days))

        date_to = fields.Date.from_string(options['date']['date_to'])
        periods = [
            (minus_days(date_to, 0), minus_days(date_to, 30)),
            (minus_days(date_to, 30), minus_days(date_to, 60)),
            (minus_days(date_to, 60), minus_days(date_to, 90)),
            (minus_days(date_to, 90), minus_days(date_to, 120)),
            (minus_days(date_to, 120), False),
        ]

        def build_result_dict(report, query_res_lines, all_total, folded_line=None):
            query_res_lines = sorted(query_res_lines, key=lambda a: a['aml_count'])
            rslt = {f'period{i}': 0 for i in range(len(periods))}
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
            query_length = len(query_res_lines) - 1
            line_total = sum(map(lambda q: q.get('amount_currency', 0), query_res_lines))
            for index, query_res in enumerate(query_res_lines):
                for i in range(len(periods)):
                    period_key = f'period{i}'
                    rslt[period_key] += query_res[period_key]
                    # Calculate the over 60
                    if i >= 2 and query_res[period_key] > 0:
                        over_60_days += query_res[period_key]
                    # if i >= 2 and query_res[period_key] < 0:
                    #     delinquent_cr += query_res[period_key]
                    if i == 4:
                    #     if index != query_length or (index == query_length and not is_total):
                        cross_amount = rslt['period0'] + rslt['period1']
                        if over_60_days and cross_amount > 0 and over_60_days > 0.2 * line_total and not folded_line:
                            cross_age_20_pct += cross_amount
                    #             totals['cross_age_20_pct'] += cross_amount
                        if query_res['amount_currency'] > 0.2 * all_total[0]['amount_currency'] and folded_line:
                    #             # 20% concentration rule
                            over_20_pct += query_res['amount_currency'] - (0.2 * all_total[0]['amount_currency'])
                    #             line_totals[2] = line['amount'] - 0.2 * all_total
                    #         if over_60_days <= 0.2 * all_total < cross_amount:
                    #             over_20_pct += cross_amount - (0.2 * total)
                    #     if index == query_length and is_total:
                    #         cross_age_20_pct = totals['cross_age_20_pct']

                if query_res['partner_id'] and self.env['res.partner'].browse(query_res['partner_id']).country_id not in \
                        [self.env.ref('base.us'), self.env.ref('base.ca'), self.env.ref('base.mx')]:
                    over_60_days = 0
                    delinquent_cr = 0
                    cross_age_20_pct = 0

            if current_groupby == 'id':
                query_res = query_res_lines[0] # We're grouping by id, so there is only 1 element in query_res_lines anyway
                currency = self.env['res.currency'].browse(query_res['currency_id'][0]) if len(query_res['currency_id']) == 1 else None

                rslt.update({
                    'amount_currency': report.format_value(query_res['amount_currency'], currency=currency),
                    'currency': currency.display_name if currency else None,
                    'account_name': query_res['account_name'][0] if len(query_res['account_name']) == 1 else None,
                    'expected_date': query_res['expected_date'][0] if len(query_res['expected_date']) == 1 else None,
                    'total': None,
                    'has_sublines': query_res['aml_count'] > 0,
                    # Updated
                    'invoice_date': query_res['invoice_date'][0] if len(query_res['invoice_date']) == 1 else None,
                    # 'total': None,
                    'over': over_60_days,
                    'cross_aged': cross_age_20_pct,
                    'conc': over_20_pct,
                    'delinquent': delinquent_cr,
                    'foreign': 0,
                    'eligible': 0,
                })
            else:
                rslt.update({
                    'invoice_date': None,
                    'total': sum(rslt[f'period{i}'] for i in range(len(periods))),
                    'over': over_60_days,
                    'cross_aged': cross_age_20_pct,
                    'conc': over_20_pct,
                    'delinquent': delinquent_cr,
                    'foreign': 0,
                    'eligible': 0,
                    'has_sublines': False,
                    'test':0,
                })

            return rslt

        # Build period table
        period_table_format = ('(VALUES %s)' % ','.join("(%s, %s, %s)" for period in periods))
        params = list(chain.from_iterable(
            (period[0] or None, period[1] or None, i)
            for i, period in enumerate(periods)
        ))
        period_table = self.env.cr.mogrify(period_table_format, params).decode(self.env.cr.connection.encoding)

        # Build query
        tables, where_clause, where_params = report._query_get(options, 'strict_range', domain=[('account_id.account_type', '=', internal_type)])

        currency_table = self.env['res.currency']._get_query_currency_table(options)
        always_present_groupby = "period_table.period_index, currency_table.rate, currency_table.precision"
        if current_groupby:
            select_from_groupby = f"account_move_line.{current_groupby} AS grouping_key,"
            groupby_clause = f"account_move_line.{current_groupby}, {always_present_groupby}"
        else:
            select_from_groupby = ''
            groupby_clause = always_present_groupby
        select_period_query = ','.join(
            f"""
                CASE WHEN period_table.period_index = {i}
                THEN %s * (
                    SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision))
                    - COALESCE(SUM(ROUND(part_debit.amount * currency_table.rate, currency_table.precision)), 0)
                    + COALESCE(SUM(ROUND(part_credit.amount * currency_table.rate, currency_table.precision)), 0)
                )
                ELSE 0 END AS period{i}
            """
            for i in range(len(periods))
        )
        tail_query, tail_params = report._get_engine_query_tail(offset, limit)

        query = f"""
            WITH period_table(date_start, date_stop, period_index) AS ({period_table})

            SELECT
                {select_from_groupby}
                %s * SUM(account_move_line.amount_currency) AS amount_currency,
                ARRAY_AGG(DISTINCT account_move_line.partner_id) AS partner_id,
                ARRAY_AGG(account_move_line.payment_id) AS payment_id,
                ARRAY_AGG(DISTINCT COALESCE(account_move_line.date_maturity, account_move_line.date)) AS report_date,
                ARRAY_AGG(DISTINCT account_move_line.expected_pay_date) AS expected_date,
                ARRAY_AGG(DISTINCT account.code) AS account_name,
                ARRAY_AGG(DISTINCT COALESCE(account_move_line.date_maturity, account_move_line.date)) AS invoice_date,
                ARRAY_AGG(DISTINCT account_move_line.currency_id) AS currency_id,
                COUNT(account_move_line.id) AS aml_count,
                ARRAY_AGG(account.code) AS account_code,
                {select_period_query}

            FROM {tables}

            JOIN account_journal journal ON journal.id = account_move_line.journal_id
            JOIN account_account account ON account.id = account_move_line.account_id
            JOIN {currency_table} ON currency_table.company_id = account_move_line.company_id

            LEFT JOIN LATERAL (
                SELECT SUM(part.amount) AS amount, part.debit_move_id
                FROM account_partial_reconcile part
                WHERE part.max_date <= %s
                GROUP BY part.debit_move_id
            ) part_debit ON part_debit.debit_move_id = account_move_line.id
            
            LEFT JOIN LATERAL (
                SELECT SUM(part.amount) AS amount, part.credit_move_id
                FROM account_partial_reconcile part
                WHERE part.max_date <= %s
                GROUP BY part.credit_move_id
            ) part_credit ON part_credit.credit_move_id = account_move_line.id

            JOIN period_table ON
                (
                    period_table.date_start IS NULL
                    OR COALESCE(account_move_line.date_maturity, account_move_line.date) <= DATE(period_table.date_start)
                )
                AND
                (
                    period_table.date_stop IS NULL
                    OR COALESCE(account_move_line.date_maturity, account_move_line.date) >= DATE(period_table.date_stop)
                )

            WHERE {where_clause}

            GROUP BY {groupby_clause}

            HAVING (
                SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision))
                - COALESCE(SUM(ROUND(part_debit.amount * currency_table.rate, currency_table.precision)), 0)
                + COALESCE(SUM(ROUND(part_credit.amount * currency_table.rate, currency_table.precision)), 0)
            ) != 0
            {tail_query}
        """

        multiplicator = -1 if internal_type == 'liability_payable' else 1
        params = [
            multiplicator,
            *([multiplicator] * len(periods)),
            date_to,
            date_to,
            *where_params,
            *tail_params,
        ]
        self._cr.execute(query, params)
        query_res_lines = self._cr.dictfetchall()
        all_total = self.get_total_for_bbc(period_table, currency_table, options['date']['date_to'], options['date']['date_from'])
        folded_line = options.get('unfolded_lines', []) and True or False
        if not current_groupby:
            return build_result_dict(report, query_res_lines, all_total, folded_line)
        else:
            rslt = []

            all_res_per_grouping_key = {}
            for query_res in query_res_lines:
                grouping_key = query_res['grouping_key']
                all_res_per_grouping_key.setdefault(grouping_key, []).append(query_res)

            for grouping_key, query_res_lines in all_res_per_grouping_key.items():
                rslt.append((grouping_key, build_result_dict(report, query_res_lines, all_total, folded_line)))

            return rslt

