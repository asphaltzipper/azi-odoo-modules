from odoo import api, fields, models
import math


class MrpPlannedOrder(models.Model):
    _inherit = "mrp.planned.order"

    e_kanban = fields.Boolean(
        related='product_id.e_kanban',
        store=True,
    )
    priority_code = fields.Integer(
        string='Priority',
        compute='_compute_priority',
    )
    main_supplier_id = fields.Many2one(
        comodel_name='res.partner',
        string='Vendor',
        related='product_mrp_area_id.main_supplier_id',
        store=True,
    )
    routing_detail = fields.Char(
        string='Routing Detail',
        compute='_compute_routing_detail',
        store=True,
    )

    @api.depends('product_id')
    def _compute_routing_detail(self):
        for record in self:
            if record.product_id:
                operations = self.env['mrp.bom'].search([('product_id', '=', record.product_id.id)]).\
                    mapped('routing_id.operation_ids')
                if operations:
                    work_center_codes = [code for code in operations.mapped('workcenter_id.code') if code]
                    record.routing_detail = ", ".join(work_center_codes)

    @api.depends('order_release_date')
    def _compute_priority(self):
        """
        Priority code must be between 2 and 9. That means we have 8 possible
        values. We assign each order a priority code based on the day it is
        scheduled to start.  Earlier orders get lower priority code, and later
        orders get higher priority code.  For example:
           - number of days spanned by selected orders = 21
           - factor = 8.0/21 = 0.38
           - order scheduled on day 1
             - priority = ceiling(0.38*1)+1 = 2
           - order scheduled on day 10
             - priority = ceiling(0.38*10)+1 = 5
           - order scheduled on day 21
             - priority = ceiling(0.38*1)+1 = 9
        """
        d_now = fields.Date.today()
        d_max = max(self.mapped('order_release_date'))
        span_days = (d_max - d_now).days
        factor = 8.0 / span_days
        for rec in self:
            day = (rec.order_release_date - d_now).days
            priority = int(math.ceil(day*factor)+1)
            rec.priority_code = min(max(priority, 2), 9)
