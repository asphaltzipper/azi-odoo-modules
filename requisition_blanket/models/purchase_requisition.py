# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import ValidationError


class PurchaseRequisitionLine(models.Model):
    _inherit = "purchase.requisition.line"

    estimated_take_down_rate = fields.Float('Estimated Take Down Rate')
    projected_reorder_date = fields.Date('Projected Reorder Date', compute='_compute_projected_reorder_date')

    @api.depends('estimated_take_down_rate', 'product_qty', 'requisition_id.ordering_date')
    def _compute_projected_reorder_date(self):
        for record in self:
            if record.requisition_id.ordering_date and record.estimated_take_down_rate:
                number_of_days = int(record.product_qty/record.estimated_take_down_rate)
                record.projected_reorder_date = record.requisition_id.ordering_date + relativedelta(days=number_of_days)

    @api.onchange('requisition_id.date_end', 'product_id', 'product_qty', 'requisition_id.first_article_lead_time', 'product_id')
    def _onchange_estimated_take_down(self):
        quantity_per_period = 0
        if self.product_id:
            end_date = datetime.now()
            start_date = end_date - relativedelta(months=12)
            moves = self.env['stock.move'].search([('product_id', '=', self.product_id.id),
                                                   ('location_dest_id.usage', '=', 'internal'),
                                                   ('date', '>=', start_date), ('date', '<=', end_date)])
            quantity_per_period = sum(moves.mapped('product_uom_qty'))
        self.estimated_take_down_rate = quantity_per_period


    @api.model
    def _get_release_date_planned(self, po=False):
        self.ensure_one()
        date_order = po.date_order if po else datetime.now()
        if date_order:
            return date_order + relativedelta(days=self.requisition_id.lead_time or 0)
        else:
            return datetime.today() + relativedelta(days=self.requisition_id.lead_time or 0)

    @api.multi
    def _prepare_purchase_order_line(self, name, product_qty=0.0, price_unit=0.0, taxes_ids=False, po=False):
        self.ensure_one()
        requisition = self.requisition_id
        date_planned = requisition.schedule_date or self._get_release_date_planned(po=po)
        return {
            'name': name,
            'product_id': self.product_id.id,
            'product_uom': self.product_id.uom_po_id.id,
            'product_qty': product_qty,
            'price_unit': price_unit,
            'taxes_id': [(6, 0, taxes_ids)],
            'date_planned': date_planned,
            'account_analytic_id': self.account_analytic_id.id,
            'analytic_tag_ids': self.analytic_tag_ids.ids,
            'move_dest_ids': self.move_dest_id and [(4, self.move_dest_id.id)] or []
        }


class PurchaseRequisition(models.Model):
    _inherit = "purchase.requisition"

    lead_time = fields.Integer(string='Lead Time', required=False)
    first_article_lead_time = fields.Integer('First-Article Lead Time')
    actual_take_down_rate = fields.Float('Actual Take Down Rate', compute='_compute_actual_take_down')

    @api.depends('line_ids.qty_ordered')
    def _compute_actual_take_down(self):
        for record in self:
            record.actual_take_down_rate = sum(record.line_ids.mapped('qty_ordered'))


class PurchaseOrder(models.Model):

    _inherit = "purchase.order"

    # short_local_date = fields.Date(string="Scheduled Date", compute='_compute_local_date')
    #
    # @api.depends('date_planned')
    # def _compute_local_date(self):
    #     for order in self:
    #         order.short_local_date = fields.Datetime.context_timestamp(self, fields.Datetime.from_string(order.date_planned))

    @api.onchange('requisition_id')
    def _onchange_requisition_id(self):
        if not self.requisition_id:
            return

        requisition = self.requisition_id
        if self.partner_id:
            partner = self.partner_id
        else:
            partner = requisition.vendor_id
        payment_term = partner.property_supplier_payment_term_id

        FiscalPosition = self.env['account.fiscal.position']
        fpos = FiscalPosition.get_fiscal_position(partner.id)
        fpos = FiscalPosition.browse(fpos)

        self.partner_id = partner.id
        self.fiscal_position_id = fpos.id
        self.payment_term_id = payment_term.id,
        self.company_id = requisition.company_id.id
        self.currency_id = requisition.currency_id.id
        if not self.origin or requisition.name not in self.origin.split(', '):
            if self.origin:
                if requisition.name:
                    self.origin = self.origin + ', ' + requisition.name
            else:
                self.origin = requisition.name
        self.notes = requisition.description
        self.date_order = fields.Datetime.now()
        self.picking_type_id = requisition.picking_type_id.id

        if requisition.type_id.line_copy != 'copy':
            return
        # Create PO lines if necessary
        order_lines = []
        for line in requisition.line_ids:
            # Compute name
            product_lang = line.product_id.with_context({
                'lang': partner.lang,
                'partner_id': partner.id,
            })
            name = product_lang.display_name
            if product_lang.description_purchase:
                name += '\n' + product_lang.description_purchase

            # Compute taxes
            if fpos:
                taxes_ids = fpos.map_tax(line.product_id.supplier_taxes_id.filtered(lambda tax: tax.company_id == requisition.company_id)).ids
            else:
                taxes_ids = line.product_id.supplier_taxes_id.filtered(lambda tax: tax.company_id == requisition.company_id).ids

            # Compute quantity and price_unit
            if line.product_uom_id != line.product_id.uom_po_id:
                product_qty = line.product_uom_id._compute_quantity(line.product_qty, line.product_id.uom_po_id)
                price_unit = line.product_uom_id._compute_price(line.price_unit, line.product_id.uom_po_id)
            else:
                product_qty = line.product_qty
                price_unit = line.price_unit

            if requisition.type_id.quantity_copy != 'copy':
                product_qty = 0

            # Create PO line
            order_line_values = line._prepare_purchase_order_line(
                name=name, product_qty=product_qty, price_unit=price_unit,
                taxes_ids=taxes_ids, po=self)
            order_lines.append((0, 0, order_line_values))
        self.order_line = order_lines


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.constrains('order_id.requisition_id', 'product_id')
    def _check_product_not_in_blanket(self):
        for record in self:
            if not record.order_id.requisition_id:
                blanket_line = self.env['purchase.requisition.line'].search([
                    ('product_id', '=', record.product_id.id),
                    ('requisition_id.state', 'not in', ('cancel', 'done')),
                    ('requisition_id.vendor_id', '=', record.order_id.partner_id.id)], limit=1)
                if blanket_line:
                    raise ValidationError('There is a blanket order %s for this product, '
                                          'please try to link the PO to this '
                                          'Blanket order' % blanket_line.requisition_id.name)
