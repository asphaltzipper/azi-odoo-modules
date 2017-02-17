# -*- coding: utf-8 -*-
# Copyright 2016 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class MrpMaterialPlanLog(models.Model):
    """
        Log the latest run for material requirements plan data
    """
    _name = "mrp.material_plan.log"
    _description = "Plan Material Log"

    type = fields.Selection(
        selection=[('info', 'Info'), ('debug', 'Debug'), ('warning', 'Warning')],
        string='Type',
        required=True,
        readonly=True
    )
    message = fields.Char(
        string='Message',
        required=True,
        readonly=True
    )
