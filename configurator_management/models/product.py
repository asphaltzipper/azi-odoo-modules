# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    default_routing_id = fields.Many2one(
        comodel_name='mrp.routing',
        string="MRP Routing",
        help="Manufacturing routing to use on variant BOMs")

    @api.multi
    def configurator_default_bom(self):
        # add a routing to the BOM
        # this depends on a patch from PR#109 on module product_configurator_mrp
        result = super(ProductTemplate, self).configurator_default_bom()
        result['routing_id'] = self.default_routing_id.id
        return result

    @api.multi
    def copy_configurable_template(self):
        self.ensure_one()

        # copy the template
        tmpl_cp = self.copy()

        # copy the attribute lines
        line_old_new_map = {}
        line_obj = self.env['product.attribute.line']
        for line in self.attribute_line_ids:
            vals = {
                'product_tmpl_id': tmpl_cp.id,
                'attribute_id': line.attribute_id.id,
                'sequence': line.sequence,
                'required': line.required,
            }
            line_cp = line_obj.create(vals)
            line_cp.value_ids = line.value_ids.ids
            line_old_new_map[line.id] = line_cp.id

        # copy config lines
        cfg_obj = self.env['product.config.line']
        for cfg in self.config_line_ids:
            vals = {
                'product_tmpl_id': tmpl_cp.id,
                'domain_id': cfg.domain_id.id,
                'attribute_line_id': line_old_new_map[cfg.attribute_line_id.id],
                'sequence': cfg.sequence,
            }
            # Values must belong to the attribute of the corresponding attribute_line set on the configuration line
            cfg_cp = cfg_obj.create(vals)
            cfg_cp.value_ids = cfg.value_ids.ids

        # copy config step lines
        step_obj = self.env['product.config.step.line']
        for step in self.config_step_line_ids:
            line_cp_list = [line_old_new_map[line_id] for line_id in step.attribute_line_ids.ids]
            vals = {
                'product_tmpl_id': tmpl_cp.id,
                'config_step_id': step.config_step_id.id,
                'sequence': step.sequence,
            }
            step_cp = step_obj.create(vals)
            step_cp.attribute_line_ids = line_cp_list
