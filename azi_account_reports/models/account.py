from bisect import bisect_left
from collections import defaultdict
from odoo import models, fields, api


class AccountAccount(models.Model):
    _inherit = 'account.account'

    account_type = fields.Selection(
        selection_add=[
            ("other_inside_advance", "Inside Advances"),
            ("other_outside_advance", "Outside Advances"),
            ("other_inventory", "Inventory"),
            ("other_accrued_liabilities", "Accrued Liabilities"),
            ("other_accrued_payroll", "Accrued Payroll"),
            ("other_sales_tax_payable", "Sales Tax Payable"),
            ("other_taxes_payable", "Taxes Payable"),
            ("other_other_receivable", "Other Receivables"),
            ("other_cogs_material", "Cost of Sales Materials"),
            ("other_cogs_overhead", "Cost of Sales Overhead"),
            ("other_cogs_salary_wages", "Cost of Sales Salary and Wages"),
            ("other_cogs_freight", "Cost of Sales Freight"),
            ("other_expense_sales_fixed", "Sales and Marketing Fixed"),
            ("other_expense_sales_salary_wages", "Sales and Marketing Salary and Wages"),
            ("other_expense_sales_variable", "Sales and Marketing Variable"),
            ("other_expense_sales_travel", "Sales and Marketing Travel"),
            ("other_expense_sales_occupancy", "Sales and Marketing Occupancy"),
            ("other_expense_sales_marketing", "Sales and Marketing Marketing"),
            ("other_expense_sales_other", "Sales and Marketing Other"),
            ("other_expense_admin_fixed", "General and Administrative Fixed"),
            ("other_expense_admin_salary_wages", "General and Administrative Salary and Wages"),
            ("other_expense_admin_variable", "General and Administrative Variable"),
            ("other_expense_admin_travel", "General and Administrative Travel"),
            ("other_expense_admin_occupancy", "General and Administrative Occupancy"),
            ("other_expense_interest", "Interest Expense"),
            ("other_expense_taxes", "Taxes Expense"),
            ("other_income_interest", "Interest Income"),
            ("other_other_income_expense", "Other Income or Expense"),
            ("other_type_taxes", "Income Taxes"),
            ("other_account_type_expenses", "General and Administrative Other"),
            ("other_gain_loss_sale_assets", "Gain or Loss on Sale of Assets"),
        ], ondelete={
            'other_inside_advance': lambda recs: recs.write({'account_type': 'off_balance'}),
            'other_outside_advance': lambda recs: recs.write({'account_type': 'off_balance'}),
            'other_inventory': lambda recs: recs.write({'account_type': 'off_balance'}),
            'other_accrued_liabilities': lambda recs: recs.write({'account_type': 'off_balance'}),
            'other_accrued_payroll': lambda recs: recs.write({'account_type': 'off_balance'}),
            'other_sales_tax_payable': lambda recs: recs.write({'account_type': 'off_balance'}),
            'other_taxes_payable': lambda recs: recs.write({'account_type': 'off_balance'}),
            'other_other_receivable': lambda recs: recs.write({'account_type': 'off_balance'}),
            'other_cogs_material': lambda recs: recs.write({'account_type': 'off_balance'}),
            'other_cogs_overhead': lambda recs: recs.write({'account_type': 'off_balance'}),
            'other_cogs_salary_wages': lambda recs: recs.write({'account_type': 'off_balance'}),
            'other_cogs_freight': lambda recs: recs.write({'account_type': 'off_balance'}),
            'other_expense_sales_fixed': lambda recs: recs.write({'account_type': 'off_balance'}),
            'other_expense_sales_salary_wages': lambda recs: recs.write({'account_type': 'off_balance'}),
            'other_expense_sales_variable': lambda recs: recs.write({'account_type': 'off_balance'}),
            'other_expense_sales_travel': lambda recs: recs.write({'account_type': 'off_balance'}),
            'other_expense_sales_occupancy': lambda recs: recs.write({'account_type': 'off_balance'}),
            'other_expense_sales_marketing': lambda recs: recs.write({'account_type': 'off_balance'}),
            'other_expense_sales_other': lambda recs: recs.write({'account_type': 'off_balance'}),
            'other_expense_admin_fixed': lambda recs: recs.write({'account_type': 'off_balance'}),
            'other_expense_admin_salary_wages': lambda recs: recs.write({'account_type': 'off_balance'}),
            'other_expense_admin_variable': lambda recs: recs.write({'account_type': 'off_balance'}),
            'other_expense_admin_travel': lambda recs: recs.write({'account_type': 'off_balance'}),
            'other_expense_interest': lambda recs: recs.write({'account_type': 'off_balance'}),
            'other_other_income_expense': lambda recs: recs.write({'account_type': 'off_balance'}),
            'other_type_taxes': lambda recs: recs.write({'account_type': 'off_balance'}),
            'other_account_type_expenses': lambda recs: recs.write({'account_type': 'off_balance'}),
            'other_gain_loss_sale_assets': lambda recs: recs.write({'account_type': 'off_balance'}),
            'other_expense_admin_occupancy': lambda recs: recs.write({'account_type': 'off_balance'}),
            'other_expense_taxes': lambda recs: recs.write({'account_type': 'off_balance'}),
            'other_income_interest': lambda recs: recs.write({'account_type': 'off_balance'}),
        })

    @api.depends('account_type')
    def _compute_internal_group(self):
        for account in self:
            if account.account_type:
                account.internal_group = 'off_balance' \
                    if account.account_type == 'off_balance' or account.account_type.startswith("other_") \
                    else account.account_type.split('_')[0]

    @api.depends('account_type')
    def _compute_include_initial_balance(self):
        for account in self:
            account.include_initial_balance = account.account_type not in \
                                              ('income', 'income_other', 'expense', 'expense_depreciation',
                                               'expense_direct_cost', 'off_balance', 'other_cogs_material',
                                               'other_cogs_overhead', 'other_cogs_salary_wages', 'other_cogs_freight',
                                               'other_expense_sales_fixed', 'other_expense_sales_salary_wages',
                                               'other_expense_sales_variable', 'other_expense_sales_travel',
                                               'other_expense_sales_occupancy', 'other_expense_sales_marketing',
                                               'other_expense_sales_other', 'other_expense_admin_fixed',
                                               'other_expense_admin_salary_wages', 'other_expense_admin_variable',
                                               'other_expense_admin_travel', 'other_expense_admin_occupancy',
                                               'other_expense_interest', 'other_expense_taxes', 'other_income_interest',
                                               'other_other_income_expense', 'other_type_taxes',
                                               'other_account_type_expenses', 'other_gain_loss_sale_assets'
                                               )
