# -*- coding: utf-8 -*-

from odoo import fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    # require routings when creating manufacturing orders
    # I wish we could just do this:
    # routing_id = fields.Many2one(required=True)
    routing_id = fields.Many2one(
        comodel_name='mrp.routing',
        string='Routing',
        readonly=True,
        # required=True,
        compute='_compute_routing',
        store=True,
        help="The list of operations (list of work centers) to produce the finished product. The routing "
             "is mainly used to compute work center costs during operations and to plan future loads on "
             "work centers based on production planning.")

    # select *
    # from mrp_bom as b
    # left join product_template as t on t.id=b.product_tmpl_id
    # where b.routing_id is null
    # and t.deprecated=false
    # and b.type='normal'
    # and b.product_id in (
