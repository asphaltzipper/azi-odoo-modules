# Copyright 2020 Matt Taylor
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api, _


class StockForecastDetailWizard(models.TransientModel):
    _name = 'stock.forecast.detail.wizard'
    _description = 'Stock Forecast Detail Wizard'

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
    )
    planned = fields.Boolean(
        string='Include Plan',
        default=True,
        help="Include MRP planned moves",
    )
    quoted = fields.Boolean(
        string='Include Quotes',
        default=False,
        help="Include customer quotations and supplier RFQs",
    )

    @api.model
    def default_get(self, fields):
        res = super(StockForecastDetailWizard, self).default_get(fields)
        if self._context and self._context.get('product_id'):
            product = self.env['product.product'].browse(self._context['product_id'])
            res['product_id'] = product.id
        return res

    @api.model
    def _prepare_confirmed_lines(self):
        lines = []

        # get stock moves
        move_domain = [
            ('product_id', '=', self.product_id.id),
            ('state', 'not in', ['cancel', 'done']),
        ]
        stock_moves = self.env['stock.move'].search(move_domain)
        for move in stock_moves:
            if move.location_id.usage == 'supplier':
                tx_type = 'po'
                qty_sign = 1
            elif move.location_id.usage == 'production':
                tx_type = 'mo'
                qty_sign = 1
            elif move.location_dest_id.usage == 'production':
                tx_type = 'pick'
                qty_sign = -1
            elif move.location_dest_id.usage == 'customer':
                tx_type = 'so'
                qty_sign = -1
            else:
                continue
            lines.append({
                'product_id': self.product_id.id,
                'tx_type': tx_type,
                'tx_date': move.date_expected,
                'product_qty': qty_sign * move.product_qty,
                'after_qty': 0,
                'late': move.date_expected < fields.datetime.now(),
                'status': 'actual',
                'origin': move.origin,
            })

        return lines

    @api.model
    def _prepare_planned_lines(self):
        lines = []

        # get mrp planned demand
        mrp_domain = [
            ('product_id', '=', self.product_id.id),
            ('mrp_origin', '=', 'mrp'),
            ('mrp_type', '=', 'd'),
        ]
        mrp_moves = self.env['mrp.move'].search(mrp_domain)
        supply_method = mrp_moves and mrp_moves[0].product_mrp_area_id.supply_method
        for move in mrp_moves:
            if supply_method == 'phantom':
                tx_type = 'ophantom'
            else:
                tx_type = 'ppick'
            lines.append({
                'product_id': self.product_id.id,
                'tx_type': tx_type,
                'tx_date': move.mrp_date,
                'product_qty': move.mrp_qty,
                'after_qty': 0.0,
                'late': move.mrp_date < fields.date.today(),
                'status': 'planned',
                'origin': move.name,
            })

        # get mrp planned supply
        planned_domain = [
            ('product_id', '=', self.product_id.id),
        ]
        planned_orders = self.env['mrp.planned.order'].search(planned_domain)
        for order in planned_orders:
            if order.mrp_qty - order.qty_released < 0.0001:
                continue
            if order.mrp_action == 'pull_push':
                tx_type = 'pxfer'
            elif order.mrp_action == 'buy':
                tx_type = 'ppo'
            elif order.mrp_action == 'manufacture':
                tx_type = 'pmo'
            elif order.mrp_action == 'phantom':
                tx_type = 'iphantom'
            else:
                import pdb
                pdb.set_trace()
                tx_type = 'ipmove'
            lines.append({
                'product_id': self.product_id.id,
                'tx_type': tx_type,
                'tx_date': order.due_date,
                'product_qty': order.mrp_qty - order.qty_released,
                'after_qty': 0,
                'late': order.due_date < fields.date.today(),
                'status': 'planned',
                'origin': order.name,
            })

        return lines

    @api.model
    def _prepare_quoted_lines(self):
        lines = []

        # get RFQs
        rfq_domain = [
            ('product_id', '=', self.product_id.id),
            ('state', '=', 'draft')
        ]
        rfq_lines = self.env['purchase.order.line'].search(rfq_domain)
        for line in rfq_lines:
            unit_qty = line.product_uom._compute_quantity(
                qty=line.product_qty,
                to_unit=line.product_id.uom_id)
            lines.append({
                'product_id': self.product_id.id,
                'tx_type': 'rfq',
                'tx_date': line.date_planned,
                'product_qty': unit_qty,
                'after_qty': 0,
                'late': line.date_planned < fields.datetime.now(),
                'status': 'planned',
                'origin': line.order_id.name,
            })

        # get quotations
        rfq_domain = [
            ('product_id', '=', self.product_id.id),
            ('state', '=', 'draft')
        ]
        rfq_lines = self.env['sale.order.line'].search(rfq_domain)
        for line in rfq_lines:
            unit_qty = line.product_uom._compute_quantity(
                qty=line.product_qty,
                to_unit=line.product_id.uom_id)
            lines.append({
                'product_id': self.product_id.id,
                'tx_type': 'quote',
                'tx_date': line.date_planned,
                'product_qty': unit_qty,
                'after_qty': 0,
                'late': line.date_planned < fields.datetime.now(),
                'status': 'planned',
                'origin': line.order_id.name,
            })

        return lines

    @api.multi
    def action_compute(self):

        # clear old analysis lines
        line_obj = self.env['stock.forecast.detail.line']
        # delete existing detail records for current user
        old_lines = line_obj.search([
            ('create_uid', '=', self._uid),
            ('product_id', '=', self.product_id.id)
        ])
        old_lines.unlink()

        # create new analysis lines
        move_lines = self._prepare_confirmed_lines()
        if self.planned:
            move_lines += self._prepare_planned_lines()
        if self.quoted:
            move_lines += self._prepare_quoted_lines()
        new_lines = line_obj.create(move_lines)

        # compute running inventory balance (qty available)
        virt_qty = self.product_id.qty_available
        # lines should be pre-sorted
        # new_lines = analysis_line.search([('create_uid', '=', self._uid), ('product_id', '=', self.product_id.id)])
        # for line in new_lines:
        for line in new_lines.sorted():
            line.write({'before_qty': virt_qty})
            virt_qty += line.product_qty
            line.write({'after_qty': virt_qty})

        search_view_id = self.env.ref('stock_forecast_detail.stock_forecast_detail_line_view_search')
        tree_view_id = self.env.ref('stock_forecast_detail.stock_forecast_detail_line_view_tree')
        form_view_id = self.env.ref('stock_forecast_detail.stock_forecast_detail_line_view_form')
        graph_view_id = self.env.ref('stock_forecast_detail.stock_forecast_detail_line_view_graph')
        pivot_view_id = self.env.ref('stock_forecast_detail.stock_forecast_detail_line_view_pivot')
        target = 'current'
        views = [
            (tree_view_id.id, 'tree'),
            (graph_view_id.id, 'graph'),
            (form_view_id.id, 'form'),
            (pivot_view_id.id, 'pivot'),
        ]
        if self._context and self._context.get('pop_graph'):
            target = 'new'
            views = [(graph_view_id.id, 'graph')]
        return {
            'name': _('Forecast Detail'),
            'domain': [('create_uid', '=', self._uid), ('product_id', '=', self.product_id.id)],
            'view_type': 'form',
            'res_model': 'stock.forecast.detail.line',
            'type': 'ir.actions.act_window',
            'views': views,
            'view_id': False,
            'target': target,
            'search_view_id': search_view_id.id,
        }
