# -*- coding: utf-8 -*-
# © 2016 Matt Taylor - Asphalt Zipper
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, models, fields, workflow
import logging
_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    #@api.multi
    #@api.depends('move_prod_id')
    #def _compute_sale_order_line(self):
    #    def get_parent_move(move):
    #        if move.move_dest_id:
    #            return get_parent_move(move.move_dest_id)
    #        return move
    #    for production in self:
    #        if production.move_prod_id:
    #            move = get_parent_move(production.move_prod_id)
    #            production.sale_order_line_id = move.procurement_id and move.procurement_id.sale_line_id and move.procurement_id.sale_line_id or False

    @api.depends('sale_order_line_id', 'move_prod_id')
    def _compute_sale_order_line(self):
        self.ensure_one()

        def get_parent_move(move):
            if move.move_dest_id:
                return get_parent_move(move.move_dest_id)
            return move

        if self.move_prod_id:
            move = get_parent_move(self.move_prod_id)
            self.sale_order_line_id = move.procurement_id and move.procurement_id.sale_line_id and move.procurement_id.sale_line_id or False

    date_planned_end = fields.Datetime(string='Due Date', required=True, copy=False, help="Planned date of completion for the manufacturing order")
    date_planned = fields.Datetime(string='Start Date')

    product_tmpl_id = fields.Many2one('product.template', string='Product Template', related='product_id.product_tmpl_id', readonly=True, store=True)
    product_category = fields.Many2one('product.category', string='Product Category', related='product_id.product_tmpl_id.categ_id', readonly=True, store=True)

    move_prod_id = fields.Many2one(readonly=False)
    sale_order_line_id = fields.Many2one('sale.order.line', compute='_compute_sale_order_line', string='Sale Order', readonly=True, store=True, help='Sales Order Line.')
    sale_order_id = fields.Many2one('sale.order', related='sale_order_line_id.order_id', string='Sale Order', readonly=True, store=True, help='Sales Order.')
    sale_partner_id = fields.Many2one('res.partner', related='sale_order_line_id.order_id.partner_id', readonly=True, string='Sale Customer', store=True, help='Sales Order Customer.')

    #sale_order_line_id = fields.Many2one('sale.order.line', compute='_compute_sale_order_line', string='Sale Order', readonly=True, help='Sales Order Line.')
    #sale_order_id = fields.Many2one('sale.order', related='sale_order_line_id.order_id', string='Sale Order', readonly=True, help='Sales Order.')
    #sale_partner_id = fields.Many2one('res.partner', related='sale_order_line_id.order_id.partner_id', readonly=True, string='Sale Customer', help='Sales Order Customer.')

    #independent_demand = fields.Boolean(string='Independent Demand', store=True, readonly=True, compute='_compute_independent_demand',
    #                                    help="When true, Manufacturing Order represents independent demand. "
    #                                         "This flag will be set if the order was not "
    #                                         "created from a procurement, or if it is "
    #                                         "associated with a Sales Order.")

    #@api.depends('id')
    #def _compute_independent_demand(self)
    #    proc_obj = self.env["procurement.order"]
    #    procs = proc_obj.search([('production_id', '=', self.id),])
    #    if self.move_prod_id or not procs:
    #        self.independent_demand = True
    #    else:
    #        self.independent_demand = False

    @api.multi
    def action_confirm_multi(self):
        _logger.info('Attempting to confirm all selected MOs')
        self.signal_workflow('button_confirm')
        #for record in self:
        #    record.signal_workflow('button_confirm')
        #    _logger.info('Confirmed MO: %s', record.name)
        # workflow.trg_validate('mrp.prod_trans_draft_picking')
        # self.action_confirm(self)

    @api.multi
    def action_cancel_multi(self):
        _logger.info('Attempting to cancel all selected MOs')
        self.signal_workflow('button_cancel')
        #for record in self:
        #    record.signal_workflow('button_cancel')
        #    _logger.info('Canceled MO: %s', record.name)
        # workflow.trg_validate('mrp.prod_trans_ready_cancel')
        # self.action_cancel(self)

