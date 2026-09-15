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

    # def _background_assign_teams(self):
    #     # Opening the cursor via 'with' automatically manages thread context and closes the cursor
    #     with self.pool.cursor() as new_cr:
    #         # Create a clean environment bound to the new cursor
    #         new_env = api.Environment(new_cr, self.env.uid, self.env.context)
    #
    #         # Call the target method using the new environment
    #         success = new_env['res.partner'].assign_sales_teams(company_id=new_env.company.id, background=True)
    #
    #         # Explicitly commit the new cursor to save changes
    #         if success:
    #             new_cr.commit()
    #         else:
    #             new_cr.rollback()
    #
    # def sales_team_assignment(self):
    #     threaded_calculation = threading.Thread(
    #         target=self._background_assign_teams, args=()
    #     )
    #     threaded_calculation.start()
    #     return {'type': 'ir.actions.act_window_close'}





    # def _background_assign_teams(self):
    #     # Opening the cursor via 'with' automatically manages thread context and closes the cursor
    #     with self.pool.cursor() as new_cr:
    #         # Bind current environment to the new cursor
    #         self = self.with_env(self.env(cr=new_cr))
    #         # Call the target method using the updated environment
    #         success = self.env['res.partner'].assign_sales_teams(company_id=self.env.company.id, background=True)
    #
    #         # Create a clean environment bound to the new cursor
    #         # new_env = api.Environment(new_cr, self.env.uid, self.env.context)
    #         # Call the target method using the new environment
    #         # success = new_env['res.partner'].assign_sales_teams(company_id=new_env.company.id, background=True)
    #
    #         # Explicitly commit the new cursor to save changes
    #         if success:
    #             new_cr.commit()
    #         else:
    #             new_cr.rollback()
    #
    #     global RUNTHREAD
    #     RUNTHREAD = False
    #     return {}
    #
    # def sales_team_assignment(self):
    #     global RUNTHREAD
    #     if not RUNTHREAD:
    #         RUNTHREAD = True
    #         threaded_calculation = threading.Thread(
    #             target=self._background_assign_teams, args=()
    #         )
    #         threaded_calculation.start()
    #     else:
    #         raise ValidationError(_('Assign Teams is already running in the background'))
    #     return {'type': 'ir.actions.act_window_close'}




    def sales_team_assignment(self):
        # self.env['res.partner'].action_reassign_all_teams()
        self.env['res.partner'].assign_sales_teams()
        return {'type': 'ir.actions.act_window_close'}
