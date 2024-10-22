from odoo import models, fields, api


class MrpRouting(models.Model):
    _name = "mrp.routing"
    _description = "Work Routing Templates"

    _sql_constraints = [
        (
            'name_unique',
            'unique (name)',
            "Routing template name must be unique",
        ),
    ]

    name = fields.Char(
        string="Name",
        required=True,
    )
    line_ids = fields.One2many(
        comodel_name="mrp.routing.line",
        inverse_name="routing_id",
        string="Work Centers",
    )
    routing_name = fields.Char(
        string="Operations Detail",
        compute="_compute_routing_name",
        readonly=True,
        store=True,
    )

    @api.depends("line_ids")
    def _compute_routing_name(self):
        for rt in self:
            wc_codes = rt.line_ids.mapped("workcenter_id.code")
            rt.routing_name = any(wc_codes) and ", ".join(wc_codes)


class MrpRoutingLine(models.Model):
    _name = "mrp.routing.line"
    _description = "Work Routing Template Operations"
    _rec_name = "workcenter_id"

    routing_id = fields.Many2one(
        comodel_name="mrp.routing",
        required=True,
    )
    workcenter_id = fields.Many2one(
        comodel_name="mrp.workcenter",
        string="Work Center",
    )
    sequence = fields.Integer(default=1)
