import threading
from odoo import api, models, tools


class StockSchedulerCompute(models.TransientModel):
    _inherit = 'stock.scheduler.compute'

    def procure_calculation(self):
        threaded_calculation = threading.Thread(target=self.with_context(procure_wizard=True)._procure_calculation_orderpoint, args=())
        threaded_calculation.start()
        return {'type': 'ir.actions.act_window_close'}
