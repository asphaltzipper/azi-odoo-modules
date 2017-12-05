# -*- coding: utf-8 -*-

from odoo import models, fields


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

    has_receipt = fields.Boolean(
        string='Receipt on File',
        help="For manual handling of paper receipts on employee purchases. "
             "Check this box when a receipt is on file.")
