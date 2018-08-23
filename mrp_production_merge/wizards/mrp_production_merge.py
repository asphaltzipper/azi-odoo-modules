# -*- coding: utf-8 -*-

from odoo import api, fields, models


class MrpProductionMerge(models.TransientModel):
    _name = 'mrp.production.merge'
    _description = 'Merge Manufacturing Orders'

    production_ids = fields.Many2many(
        comodel_name='mrp.production',
        string='Manufacturing Orders',
        required=True)

    order_count = fields.Integer(
        string="Order Count",
        readonly=True)

    product_count = fields.Integer(
        string="Product Count",
        readonly=True)

    is_error = fields.Boolean(
        string="Errors Found",
        readonly=True)

    error_message = fields.Text(
        string="Errors",
        readonly=True)

    @api.model
    def default_get(self, fields):
        defaults = super(MrpProductionMerge, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', False)
        domain = [('id', 'in', active_ids), ('state', 'in', ['confirmed', 'planned'])]
        res = self.env['mrp.production'].search(domain)
        defaults['production_ids'] = [(6, 0, [rec.id for rec in res])]
        defaults['order_count'] = len(res)
        defaults['product_count'] = len(res.mapped('product_id'))
        defaults['is_error'], defaults['error_message'] = self._check_errors(res)
        return defaults

    @api.model
    def _check_errors(self, productions):
        is_error = False
        error_message = 'The following MOs are partially complete:\n'
        for production in productions:
            if 'done' in (production.move_raw_ids | production.move_finished_ids).mapped('state'):
                is_error = True
                error_message = error_message + ', ' + production.name
        if is_error:
            return is_error, error_message
        return is_error, 'Good to go'

    @api.multi
    def do_merge(self):
        if not self.production_ids:
            return

        products = self.production_ids.mapped('product_id')
        for product_id in products:
            productions = self.production_ids.filtered(lambda x: x.product_id == product_id).sorted(key=lambda l: l.date_planned_start)
            if not len(productions) > 1:
                continue
            main_production = productions[0]
            new_qty = main_production.product_qty

            for production in productions[1:]:
                new_qty += production.product_qty
                production.action_cancel()
                production.unlink()

            change_wiz = self.env['change.production.qty'].create({'mo_id': main_production.id, 'product_qty': new_qty})
            change_wiz.change_prod_qty()

        return {'type': 'ir.actions.act_window_close'}
