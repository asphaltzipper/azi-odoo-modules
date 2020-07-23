from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools import float_round


class MrpProduction(models.Model):
    _inherit = "mrp.production"
    # This assumes that the produced product is measured in units

    kit_done = fields.Boolean(
        string="Kit Done",
        compute="_compute_kit_done",
        store=True,
        help="Parts kit is complete, and has been moved to starting workcenter",
    )
    kit_assigned_qty = fields.Integer(
        string="Kit Qty",
        required=True,
        default=0,
        help="Number of component kits assigned to this order",
    )
    kit_avail_qty = fields.Integer(
        related="product_id.mfg_kit_qty",
    )

    @api.constrains('kit_assigned_qty')
    def _check_kit_assigned_qty(self):
        for rec in self:
            if rec.kit_assigned_qty > float_round(
                    rec.product_qty, precision_digits=0):
                raise UserError(_("Can't assign more kits than required"))
            if rec.kit_assigned_qty < 0:
                raise UserError(_("Can't assign negative number of kits"))

    @api.multi
    def write(self, vals):
        if 'kit_assigned_qty' in vals:
            kit_change_qty = vals['kit_assigned_qty'] - self.kit_assigned_qty
            new_avail_qty = self.kit_avail_qty - kit_change_qty
            self.product_id.mfg_kit_qty = max(0, new_avail_qty)
        return super(MrpProduction, self).write(vals)

    @api.depends('kit_assigned_qty', 'product_qty')
    def _compute_kit_done(self):
        for rec in self:
            rec.kit_done = rec.kit_assigned_qty >= rec.product_qty

    @api.model
    def create(self, values):
        if values.get('product_id') and values.get('product_qty'):
            product = self.env['product.product'].search([('id', '=', values['product_id'])])
            if product.mfg_kit_qty:
                to_assign = min(product.mfg_kit_qty, values['product_qty'])
                to_assign = int(float_round(to_assign, precision_digits=0))
                values['kit_assigned_qty'] = to_assign
                product.mfg_kit_qty = max(0, product.mfg_kit_qty - to_assign)
        return super(MrpProduction, self).create(values)

    @api.multi
    def action_cancel(self):
        for rec in self:
            if rec.kit_assigned_qty > 0:
                rec.kit_assigned_qty = 0
        return super(MrpProduction, self).action_cancel()
