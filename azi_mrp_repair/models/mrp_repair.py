import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class Repair(models.Model):
    _inherit = 'repair.order'

    stock_valuation_layer_id = fields.Many2one(
        comodel_name='stock.valuation.layer',
        string='Inventory Revaluation',
        copy=False,
    )

    def action_repair_end(self):
        # create inventory revaluation for repaired product
        res = super(Repair, self).action_repair_end()

        production_loc = self.env['stock.location'].search(
            [('usage', '=', 'production'), ('company_id', '=', self.company_id.id)],
            limit=1,
        )
        valuation_in_account = production_loc.valuation_in_account_id
        valuation_out_account = production_loc.valuation_out_account_id

        for repair in self:
            # skip this repair order if the following conditions are met
            if (
                repair.partner_id
                or repair.location_id.usage != 'internal'
                or repair.product_id.categ_id.property_cost_method != 'fifo'
                or repair.product_id.categ_id.property_valuation != 'real_time'
            ):
                continue

            # verify there is a value change
            valued_lines = repair.operations.filtered(
                lambda x: x.move_id.stock_valuation_layer_ids
            )
            svl_ids = valued_lines.mapped("move_id.stock_valuation_layer_ids")
            value_change = -1 * sum(svl_ids.mapped('value'))
            precision = repair.company_id.currency_id.decimal_places
            if float_is_zero(value_change, precision):
                continue

            # verify the external location is production
            if valued_lines.filtered(
                lambda o: (o.type == 'add' and o.location_dest_id != production_loc)
                          or (o.type == 'remove' and o.location_id != production_loc)
            ):
                raise UserError(_("Can't create revaluation: All parts must move to or "
                                  "from the production location"))

            # run the revaluation wizard
            journal_id = repair.product_id.categ_id.property_stock_journal
            account_id = (
                (value_change > 0)
                and valuation_in_account
                or valuation_out_account
            )
            wiz_vals = {
                'company_id': repair.company_id.id,
                'product_id': repair.product_id.id,
                'lot_id': repair.lot_id.id,
                'added_value': value_change,
                'account_journal_id': journal_id.id,
                'account_id': account_id.id,
                'reason': _("Repaired on %s", repair.name),
            }
            wiz = self.env['stock.valuation.layer.revaluation'].create(wiz_vals)
            wiz.action_validate_revaluation()

            wiz.stock_valuation_layer_id.stock_move_id = repair.move_id
            repair.stock_valuation_layer_id = wiz.stock_valuation_layer_id

        return res


class RepairLine(models.Model):
    _inherit = 'repair.line'

    @api.onchange('type', 'repair_id')
    def onchange_operation_type_azi(self):
        if self.type == 'remove':
            self.price_unit = 0.0
            self.tax_id = False

            args = (
                self.repair_id.company_id
                and [('company_id', '=', self.repair_id.company_id.id)]
                or []
            )
            warehouse = self.env['stock.warehouse'].search(args, limit=1)
            self.location_dest_id = warehouse.lot_stock_id

            production_loc = self.env['stock.location'].search(
                [
                    ('usage', '=', 'production'),
                    ('company_id', 'in', [self.repair_id.company_id.id, False]),
                ],
                limit=1,
            )
            self.location_id = production_loc
