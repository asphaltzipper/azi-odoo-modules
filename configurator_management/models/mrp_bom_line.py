from odoo import api, fields, models
from itertools import groupby


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    def _skip_bom_line(self, product):
        """ Revert to core functionality """
        if self.attribute_value_ids:
            for att, att_values in groupby(self.attribute_value_ids, lambda l: l.attribute_id):
                values = self.env['product.attribute.value'].concat(*list(att_values))
                if not (product.attribute_value_ids & values):
                    return True
        return False
