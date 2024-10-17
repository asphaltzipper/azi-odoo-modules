from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from datetime import datetime, date


class PurchaseRequisitionLine(models.Model):
    _inherit = "purchase.requisition.line"

    estimated_take_down_rate = fields.Float(
        string='Est Qty/Month',
        help="Estimated quantity of consumption per month",
    )
    actual_take_down_rate = fields.Float(
        string='Actual Qty/Month',
        compute='_compute_actual_take_down',
        help="Actual quantity of consumption per month",
    )
    projected_reorder_date = fields.Date(
        string='Projected Reorder Date',
        compute='_compute_projected_reorder_date',
        help="Predicted date on which a new blanket order will need to be "
             "created, based on the greater of Est Qty/Month or Actual Qty/Month",
    )
    date_end = fields.Datetime(
        related='requisition_id.date_end',
    )
    ordering_date = fields.Date(
        related='requisition_id.ordering_date',
    )
    lead_time = fields.Integer(
        related='requisition_id.lead_time',
    )

    @api.depends('date_end', 'estimated_take_down_rate', 'product_qty', 'ordering_date')
    def _compute_projected_reorder_date(self):
        for record in self:
            if record.ordering_date:
                rate = max(record.estimated_take_down_rate or 0, record.actual_take_down_rate or 0)/30
                if rate == 0:
                    record.projected_reorder_date = False
                else:
                    number_of_days = int(record.product_qty/rate)
                    record.projected_reorder_date = record.ordering_date + relativedelta(days=number_of_days)
            else:
                record.projected_reorder_date = False

    @api.onchange('date_end', 'product_id', 'product_qty', 'lead_time', 'product_id')
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

    @api.depends('qty_ordered', 'date_end', 'ordering_date', 'requisition_id.lead_time')
    def _compute_actual_take_down(self):
        for record in self:
            date_order = record.requisition_id.ordering_date or False
            if date_order:
                date_end = record.requisition_id.date_end and record.requisition_id.date_end.date() or False
                if not date_end or date_end > date.today():
                    date_end = date.today()
                date_start = date_order + relativedelta(days=record.lead_time)
                if date_start > date_end:
                    no_of_days = (date_end - date_order).days
                else:
                    no_of_days = (date_end - date_start).days
                if no_of_days == 0:
                    record.actual_take_down_rate = 0
                else:
                    record.actual_take_down_rate = 30 * record.qty_ordered / no_of_days
            else:
                record.actual_take_down_rate = 0

    @api.model
    def _get_release_date_planned(self, po=False):
        self.ensure_one()
        date_order = po.date_order if po else datetime.now()
        if date_order:
            return date_order + relativedelta(days=self.requisition_id.release_lead_time or 0)
        else:
            return datetime.today() + relativedelta(days=self.requisition_id.release_lead_time or 0)

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
            'date_planned': datetime.fromordinal(date_planned.toordinal()),  # convert from date to datetime
            'account_analytic_id': self.account_analytic_id.id,
            'analytic_tag_ids': self.analytic_tag_ids.ids,
            'move_dest_ids': self.move_dest_id and [(4, self.move_dest_id.id)] or []
        }


class PurchaseRequisition(models.Model):
    _inherit = "purchase.requisition"

    description = fields.Text(
        tracking=True,
    )

    lead_time = fields.Integer(
        string='First-Article Lead Time',
        required=True,
        help="Number of days from blanket order to availability of first-article",
    )
    release_lead_time = fields.Integer(
        string='Release Lead Time',
        required=True,
        help="Number of days from order to delivery for a release of the product",
    )
    projected_reorder_date = fields.Date('Projected Reorder Date', compute='_compute_projected_reorder_date')
    is_blanket = fields.Boolean('Is Blanket Order?', compute='_compute_is_blanket')

    @api.depends('line_ids.projected_reorder_date')
    def _compute_projected_reorder_date(self):
        for record in self:
            projected_reorder_date = record.line_ids.filtered(lambda x: x.projected_reorder_date).mapped(
                'projected_reorder_date')
            if projected_reorder_date and len(projected_reorder_date):
                record.projected_reorder_date = min(projected_reorder_date)
            else:
                record.projected_reorder_date = False

    @api.depends('type_id')
    def _compute_is_blanket(self):
        for record in self:
            if record.type_id and record.type_id.name == 'Blanket Order':
                record.is_blanket = True
