from odoo import api, models, fields


class StockInventoryKanban(models.Model):
    _inherit = 'stock.inventory.kanban'

    @api.multi
    def print_missing_kanbans_2x1(self):
        """ Print the missing kanban cards in order to restore them
        """
        self.ensure_one()
        return self.env.ref(
            'azi_stock_request_kanban.action_report_kanban_label_2x1').report_action(
            self.missing_kanban_ids
        )
