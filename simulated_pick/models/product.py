# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.osv import expression


class Product(models.Model):
    _inherit = "product.product"

    @api.multi
    def get_procurement_action(self, location=None):
        """
        Return true if this product should be manufactured, based on procurement rule
        We may want to add an interface to the procurement.rule model, so users can change the sequence
        :returns procurement.rule.action :
         - move
         - buy
         - manufacture
         - ...
         - unknown
        """
        self.ensure_one()

        domain = []
        if location:
            # set domain on locations
            parent_locations = self.env['stock.location']
            child_location = location
            while child_location:
                parent_locations |= child_location
                child_location = child_location.location_id
            domain = [('location_id', 'in', parent_locations.ids)]

        # try finding a rule on product routes
        Pull = self.env['procurement.rule']
        rule = self.env['procurement.rule']
        product_routes = self.route_ids | self.categ_id.total_route_ids
        if product_routes:
            rule = Pull.search(expression.AND([[('route_id', 'in', product_routes.ids)], domain]),
                               order='route_sequence, sequence', limit=1)

        # try finding a rule on warehouse routes
        if not rule:
            warehouse = self.env['stock.warehouse'].search([], order='id', limit=1)
            warehouse_routes = warehouse.route_ids
            if warehouse_routes:
                rule = Pull.search(expression.AND([[('route_id', 'in', warehouse_routes.ids)], domain]),
                                   order='route_sequence, sequence', limit=1)

        # try finding a rule that handles orders with no route
        if not rule:
            rule = Pull.search(expression.AND([[('route_id', '=', False)], domain]), order='sequence', limit=1)

        if not rule:
            return 'unknown'
        return rule.action
