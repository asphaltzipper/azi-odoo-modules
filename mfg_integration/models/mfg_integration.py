# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MfgWorkImport(models.Model):
    _name = 'mfg.work.import'

    date_import = fields.Datetime(
        string="Import Date")

    detail_ids = fields.One2many(
        comodel_name='mfg.detail.import',
        inverse_name='import_id')

    # batch_ids = fields.One2many(
    #     comodel_name='mfg.batch.import',
    #     inverse_name='import_id')

    is_closed = fields.Boolean(
        string="Closed")

    user_id = fields.Many2one(
        comodel_name='res.users')

    work_hours = fields.Float(
        string="Work Hours")

    def button_apply_work(self):
        # gather all products produced
        # adjust MO qty to actual produced
        # divide work_hours across products by percentage, weighted against beam-time (one of Jeremy's columns)
        # create labor time entries
        # complete work orders
        # complete manufacturing orders
        # for work in self:
        #     for detail in work.detail_ids:
        #         ...
        pass


class MfgDetailImport(models.Model):
    _name = 'mfg.detail.import'

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product')

    workorder_id = fields.Many2one(
        comodel_name='mrp.workorder',
        string='Workorder')

    import_id = fields.Many2one(
        comodel_name='mfg.work.import')

    # add one field for each column in the spreadsheet from jeremy

    def _get_latest_import(self):
        work_import = self.env['mfg.work.import'].search([('is_closed', '=', False)], order='date_import DESC', limit=1)
        return work_import.id

    def create(self, vals):
        vals['import_id'] = vals.get('import_id', self._get_latest_import())
        super(MfgDetailImport, self).create(vals)


# class MfgBatchImport(models.Model):
#     _name = 'mfg.batch.import'
#
#     product_id = fields.Many2one()
#     import_id = fields.Many2one()
#     # one field for each column jeremy gives me
