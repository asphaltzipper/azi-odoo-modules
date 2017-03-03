# -*- coding: utf-8 -*-

from lxml import etree

from odoo.osv import orm
from odoo import models, fields, api, _
from odoo.exceptions import Warning, ValidationError


class FreeSelection(fields.Selection):

    def convert_to_cache(self, value, record, validate=True):
        return super(FreeSelection, self).convert_to_cache(
            value=value, record=record, validate=False)


class ProductConfigurator(models.TransientModel):
    _inherit = 'product.configurator'
    _name = 'product.configurator.ms'

    @api.multi
    def action_config_done(self):
        """Parse values and execute final code before closing the wizard"""
        custom_vals = {
            l.attribute_id.id:
                l.value or l.attachment_ids for l in self.custom_value_ids
        }

        if self.product_id:
            self.product_id.write({
                'attribute_value_ids': [(6, 0, self.value_ids.ids)],
                'value_custom_ids': [(6, 0, custom_vals)]
            })
            self.unlink()
            return
        try:
            variant = self.product_tmpl_id.create_variant(
                self.value_ids.ids, custom_vals)
        except:
            raise ValidationError(
                _('Invalid configuration! Please check all '
                  'required steps and fields.')
            )

        sl = self.env['mrp.schedule.line'].browse(self.env.context.get('active_id'))

        sl.write({'product_id': variant.id})

        self.unlink()
        return
