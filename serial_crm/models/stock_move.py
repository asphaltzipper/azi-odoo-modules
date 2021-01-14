from odoo import models, fields, api, _


class StockMove(models.Model):
    _inherit = "stock.move"

    account_move_cost = fields.Float(
        string="Acct Cost",
        compute='_compute_account_move_cost',
    )
    account_cost_unit = fields.Float(
        string="Acct Unit Cost",
        compute='_compute_account_move_cost',
    )

    def _compute_account_move_cost(self):
        for move in self:
            stock_valuation_account = move.product_id.product_tmpl_id.get_product_accounts().get('stock_valuation')
            if not stock_valuation_account:
                continue
            account_moves = self.env['account.move'].search([('stock_move_id', '=', move.id)])
            if not account_moves:
                continue
            aml_domain = [
                ('move_id', 'in', account_moves.ids),
                ('account_id', '=', stock_valuation_account.id),
                ('product_id', '=', move.product_id.id),
            ]
            account_move_lines = self.env['account.move.line'].search(aml_domain)
            if not account_move_lines:
                continue
            aml_cost = sum(account_move_lines.mapped('balance'))
            move.account_move_cost = aml_cost
            move.account_cost_unit = aml_cost / move.product_qty


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    account_cost_unit = fields.Float(
        related='move_id.account_cost_unit',
    )
