# -*- coding: utf-8 -*-

from odoo import models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def open_wo_produce(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            'mrp_wo_produce.act_mrp_wo_produce_wizard')
        return action
