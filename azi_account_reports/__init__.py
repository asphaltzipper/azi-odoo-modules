# -*- coding: utf-8 -*-

import models
from odoo import api, SUPERUSER_ID


def _set_update(cr, registry):
    """apply noupdate flag on all data imported by this module"""
    env = api.Environment(cr, SUPERUSER_ID, {})
    data = env['ir.model.data'].search([('module', '=', 'azi_account_reports'), ('model', '=', 'account.account.type')])
    for dat in data:
        dat.noupdate = False
    other = env['ir.model.data'].search([('module', '=', 'account'), ('name', '=', 'data_account_type_expenses')])
    other.noupdate = False

def _set_noupdate(cr, registry):
    """apply noupdate flag on all data imported by this module"""
    env = api.Environment(cr, SUPERUSER_ID, {})
    data = env['ir.model.data'].search([('model', '=', 'account.account.type')])
    for dat in data:
        if dat.model == 'account.account.type':
            dat.noupdate = True
