# -*- coding: utf-8 -*-
# Copyright 2017 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models

import threading


class SalesTeamAssign(models.TransientModel):
    _name = 'sales.team.assign'
    _description = 'Assign Sales Teams to Customers'

    def _sales_team_assign(self):
        with api.Environment.manage():
            # As this function is in a new thread, I need to open a new cursor, because the old one may be closed
            new_cr = self.pool.cursor()
            self = self.with_env(self.env(cr=new_cr))
            self.env['res.partner']._assign_all_customers(
                use_new_cursor=new_cr.dbname,
                company_id=self.env.user.company_id.id)
            new_cr.close()
            return {}

    def sales_team_assignment(self):
        threaded_calculation = threading.Thread(target=self._sales_team_assign, args=())
        threaded_calculation.start()
        return {'type': 'ir.actions.act_window_close'}
