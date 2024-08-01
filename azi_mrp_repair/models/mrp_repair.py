import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare


class Repair(models.Model):
    _inherit = 'repair.order'

    do_revaluation = fields.Boolean(
        string='Do Revaluation',
        copy=False,
        default=True,
    )
    # TODO Revaluation
    # inventory_revaluation_id = fields.Many2one(
    #     comodel_name='stock.inventory.revaluation',
    #     string='Inventory Revaluation',
    #     copy=False,
    # )

    # TODO Revaluation
    # def action_repair_done(self):
    #     # create inventory revaluation for repaired product
    #     res = super(Repair, self).action_repair_done()
    #
    #     production_loc = self.env['stock.location'].search([('usage', '=', 'production')], limit=1)
    #     valuation_in_account = production_loc.valuation_in_account_id
    #     valuation_out_account = production_loc.valuation_out_account_id
    #
    #     for repair in self:
    #         # skip this repair order if the following conditions are met
    #         if not repair.do_revaluation:
    #             continue
    #         if repair.partner_id:
    #             continue
    #         if repair.location_id.usage != 'internal':
    #             continue
    #         if repair.product_id.categ_id.property_cost_method != 'fifo':
    #             continue
    #         valued_lines = repair.operations.filtered(lambda o: o.move_id.account_move_ids)
    #         value_change = -1 * sum(valued_lines.mapped('move_id.value'))
    #         if not value_change:
    #             continue
    #
    #         # verify the external location is production
    #         if valued_lines.filtered(lambda o:
    #                                  (o.type == 'add' and o.location_dest_id != production_loc) or
    #                                  (o.type == 'remove' and o.location_id != production_loc)):
    #             raise UserError("Can't create revaluation: All parts must move to or from the production location")
    #
    #         reval_vals = {
    #             'revaluation_type': 'inventory_value',
    #             'product_id': repair.product_id.id,
    #             'journal_id': self.env['account.journal'].search([('type', '=', 'general')], limit=1).id,
    #             'increase_account_id': valuation_out_account.id,
    #             'decrease_account_id': valuation_in_account.id,
    #             'remarks': f"Repaired on {repair.name}",
    #         }
    #         reval = self.env['stock.inventory.revaluation'].create(reval_vals)
    #
    #         # use the wizard to find stock moves to revalue
    #         wiz_vals = {
    #             'revaluation_id': reval.id,
    #             'product_id': repair.product_id.id,
    #         }
    #         if repair.lot_id:
    #             wiz_vals['lot_id'] = repair.lot_id.id
    #         get_moves_wiz = self.env['stock.inventory.revaluation.get.moves'].create(wiz_vals)
    #         get_moves_wiz.process()
    #         if not reval.reval_move_ids:
    #             raise UserError("No inbound moves were found to revalue")
    #
    #         # set new value
    #         if repair.product_id.tracking == 'serial':
    #             if len(reval.reval_move_ids) == 1:
    #                 if reval.reval_move_ids[0].current_value + value_change < 0:
    #                     raise UserError("Can't create revaluation because the new value would be less than zero")
    #                 reval.reval_move_ids[0].new_value = reval.reval_move_ids[0].current_value + value_change
    #             else:
    #                 raise UserError("Multiple inbound moves to revalue:\n"
    #                                 "Automatic revaluation, when repairing a serialized product, is only supported "
    #                                 "when a single inbound move is found. You will need to force the repair order to "
    #                                 "complete, then create the revaluation manually.")
    #         else:
    #             qty_to_assign = repair.product_qty
    #             amt_to_assign = value_change
    #             for move in reval.reval_move_ids.sorted(key=lambda x: x.in_date):
    #                 if qty_to_assign <= move.qty:
    #                     if move.current_value + amt_to_assign < 0:
    #                         raise UserError("Can't create revaluation because the new value would be less than zero")
    #                     move.new_value = move.current_value + amt_to_assign
    #                     qty_to_assign = 0
    #                     amt_to_assign = 0
    #                     break
    #                 else:
    #                     if move.current_value + amt_to_assign * move.qty / qty_to_assign < 0:
    #                         raise UserError("Can't create revaluation because the new value would be less than zero")
    #                     move.new_value = move.current_value + amt_to_assign * move.qty / qty_to_assign
    #                     qty_to_assign -= move.qty
    #                     amt_to_assign -= amt_to_assign * move.qty / qty_to_assign
    #             if qty_to_assign > 0:
    #                 raise UserError("Couldn't find enough remaining quantity on inbound moves to revalue. You must be "
    #                                 "trying to repair more than you have in stock.")
    #
    #         # post the revaluation
    #         repair.inventory_revaluation_id = reval
    #
    #     return res


class RepairLine(models.Model):
    _inherit = 'repair.line'

    @api.onchange('type', 'repair_id')
    def onchange_operation_type_azi(self):
        if self.type == 'remove':
            self.price_unit = 0.0
            self.tax_id = False
            args = self.repair_id.company_id and [('company_id', '=', self.repair_id.company_id.id)] or []
            warehouse = self.env['stock.warehouse'].search(args, limit=1)
            self.location_dest_id = warehouse.lot_stock_id
            self.location_id = self.env['stock.location'].search([('usage', '=', 'production')], limit=1).id
