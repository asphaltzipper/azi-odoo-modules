# -*- coding: utf-8 -*-
# (c) 2016 Matt Taylor
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MrpScheduleLine(models.Model):
    _inherit = "mrp.schedule.line"

    config_ok = fields.Boolean(
        string="Configurable",
        related='product_id.config_ok',
    )
    config_name = fields.Char(
        string='Config Name',
        related='product_id.config_name',
    )

    @api.multi
    def reconfigure_product(self):
        """ Creates and launches a product configurator wizard with a linked
        template and variant in order to re-configure a existing product. It is
        esetially a shortcut to pre-fill configuration data of a variant"""

        cfg_steps = self.product_id.product_tmpl_id.config_step_line_ids
        active_step = str(cfg_steps[0].id) if cfg_steps else 'configure'

        wizard_obj = self.env['product.configurator']
        wizard = wizard_obj.create({
            'product_id': self.product_id.id,
            'state': active_step
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.configurator',
            'name': "Configure Product",
            'view_mode': 'form',
            'context': dict(
                self.env.context,
                wizard_id=wizard.id,
            ),
            'target': 'new',
            'res_id': wizard.id,
        }
