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
            # don't use .mapped() because it returns unique codes only, and routings
            # may pass through the same workcenter more than once
            wc_codes = [x.workcenter_id.code for x in rt.line_ids]
            rt.routing_name = any(wc_codes) and ", ".join(wc_codes)

    def apply_to_bom(self, bom):
        # TODO: keep/modify existing operations
        self.ensure_one()
        bom.ensure_one()
        # remove all operations
        bom.operation_ids.action_archive()
        # add all operations
        vals_list = []
        for line in self.lines:
            vals_list.append({
                "bom_id": bom.id,
                "name": line.workcenter_id.code,
                "workcenter_id": line.workcenter_id.id,
                "time_mode": "auto",
            })
        self.env['mrp.routing.workcenter'].create(vals_list)


class MrpRoutingLine(models.Model):
    _name = "mrp.routing.line"
    _description = "Work Routing Template Operations"
    _rec_name = "workcenter_id"
    _order = "sequence, workcenter_sequence"

    routing_id = fields.Many2one(
        comodel_name="mrp.routing",
        required=True,
    )
    workcenter_id = fields.Many2one(
        comodel_name="mrp.workcenter",
        string="Work Center",
    )
    workcenter_sequence = fields.Integer(
        related="workcenter_id.sequence",
        string="WC Sequence",
    )
    sequence = fields.Integer(
        string="Sequence",
        default=1,
    )
