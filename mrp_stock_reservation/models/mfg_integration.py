# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class MfgWorkDetail(models.Model):
    _inherit = 'mfg.work.detail'

    def action_mrp_reservation_form(self):
        self.ensure_one()
        if self.product_id:
            return self.product_id.action_mrp_reservation_form()
