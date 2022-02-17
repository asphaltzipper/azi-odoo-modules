from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

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
