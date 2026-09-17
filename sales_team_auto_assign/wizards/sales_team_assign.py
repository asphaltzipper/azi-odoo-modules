# -*- coding: utf-8 -*-
# Copyright 2017 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, _
import threading
from odoo.exceptions import ValidationError

RUNTHREAD = False


class SalesTeamAssign(models.TransientModel):
    _name = 'sales.team.assign'
    _description = 'Assign Sales Teams to Customers'

    def sales_team_assignment(self):
        # self.env['res.partner'].action_reassign_all_teams()
        self.env['res.partner'].assign_sales_teams()
        return {'type': 'ir.actions.act_window_close'}
