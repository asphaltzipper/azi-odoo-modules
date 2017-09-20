# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
from dateutil.relativedelta import relativedelta



class PurchaseRequisitionLine(models.Model):

    _inherit = "purchase.requisition.line"

    @api.model
    def _get_release_date_planned(self, po=False):
        self.ensure_one()
        date_order = po.date_order if po else self.order_id.date_order
        if date_order:
            return datetime.strptime(date_order, DEFAULT_SERVER_DATETIME_FORMAT) + relativedelta(days=self.requisition_id.lead_time or 0)
        else:
            return datetime.today() + relativedelta(days=self.requisition_id.lead_time or 0)

    @api.multi
    def _prepare_purchase_order_line(self, name, product_qty=0.0, price_unit=0.0, taxes_ids=False, partner_id=False, po=False):
        self.ensure_one()
        requisition = self.requisition_id
        seller = self.product_id._select_seller(
            partner_id=partner_id,
            quantity=product_qty,
            date=requisition.schedule_date or fields.Date.today(),
            uom_id=self.product_id.uom_po_id)
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
        }


class PurchaseRequisition(models.Model):
    _inherit = "purchase.requisition"

    lead_time = fields.Integer(string='Lead Time', required=False)


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
        currency = partner.property_purchase_currency_id or requisition.company_id.currency_id

        FiscalPosition = self.env['account.fiscal.position']
        fpos = FiscalPosition.get_fiscal_position(partner.id)
        fpos = FiscalPosition.browse(fpos)

        self.partner_id = partner.id
        self.fiscal_position_id = fpos.id
        self.payment_term_id = payment_term.id,
        self.company_id = requisition.company_id.id
        self.currency_id = currency.id
        self.origin = requisition.name
        self.partner_ref = requisition.name # to control vendor bill based on agreement reference
        self.notes = requisition.description
        self.date_order = requisition.date_end or fields.Datetime.now()
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

            # Compute price_unit in appropriate currency
            if requisition.company_id.currency_id != currency:
                price_unit = requisition.company_id.currency_id.compute(price_unit, currency)

            # Create PO line
            order_line_values = line._prepare_purchase_order_line(
                name=name, product_qty=product_qty, price_unit=price_unit,
                taxes_ids=taxes_ids, partner_id=self.partner_id, po=self)
            order_lines.append((0, 0, order_line_values))
        self.order_line = order_lines

