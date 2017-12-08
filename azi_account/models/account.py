# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountReconcileModel(models.Model):
    _inherit = 'account.reconcile.model'

    analytic_tag_ids = fields.Many2many(
        comodel_name='account.analytic.tag',
        string='Analytic tags')

    second_analytic_tag_ids = fields.Many2many(
        comodel_name='account.analytic.tag',
        string='Second Analytic tags')


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    receipt_status = fields.Selection(
        selection=[
            ('yes', 'Yes'),
            ('no', 'No'),
            ('na', 'N/A')],
        string='Receipt on File',
        default='no',
        required=True,
        help="For manual handling of paper receipts on employee purchases. "
             "Check this box when a receipt is on file.")


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    @api.multi
    def action_counterpart_lines(self):

        ctx = self._context.copy()
        ctx.pop('group_by', None)
        ctx.update({
            'search_default_journal_id': self.id,
        })

        journals = self.search([('type', 'in', ['bank', 'cash'])])
        accounts = journals.mapped('default_credit_account_id')
        account_ids = accounts.ids

        domain = [
            ('account_id', 'not in', account_ids),
            ('journal_id', 'in', journals.ids),
        ]

        action_name = "action_move_lines_counterpart"
        ir_model_obj = self.env['ir.model.data']
        model, action_id = ir_model_obj.get_object_reference('azi_account', action_name)
        [action] = self.env[model].browse(action_id).read()
        action['domain'] = domain
        action['context'] = ctx

        return action
