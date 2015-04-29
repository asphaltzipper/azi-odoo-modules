# -*- coding: utf-8 -*-

import threading
from openerp import models, fields, api, SUPERUSER_ID
from openerp.api import Environment


class procurement_order_run(models.Model):
    _name = 'procurement.order.run'
    _description = 'Run Procurement(s)'

    def _get_active_ids(self, cr, uid, context=None):
        context = context or {}
        return context.get('active_ids', False)

    procurement_ids = fields.Many2many('procurement.order', required=True, default=lambda self: self._get_active_ids())

    def _procurement_run_thread(self, cr, uid, ids, context=None):
        with Environment.manage():
            proc_obj = self.pool.get('procurement.order')
            new_cr = self.pool.cursor()
            proc_obj.run_procurement(new_cr, uid, context.get('active_ids'), use_new_cursor=new_cr.dbname, context=context)
            new_cr.close()
            return {}

    def procurement_run(self, cr, uid, ids, context=None):
        threaded_calculation = threading.Thread(target=self._procurement_run_thread, args=(cr, uid, ids, context))
        threaded_calculation.start()
        return {'type': 'ir.actions.act_window_close'}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
