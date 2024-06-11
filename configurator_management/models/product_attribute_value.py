from odoo import models, fields, api


class ProductTemplateAttributeValue(models.Model):
    _inherit = 'product.template.attribute.value'

    code = fields.Char(
        string='Code',
        help='Short descriptive code to be concatenated into a variant code',
    )

    @api.model
    def get_variant_code(self, attributes=None):
        if not attributes:
            return " / ".join(
                [v.code for v in self.sorted(lambda x: x.attribute_id.sequence) if v.code]
            )
        else:
            return " / ".join(
                [v.code for v in self.sorted(lambda x: x.attribute_id.sequence) if v.code and v.attribute_id in attributes]
            )
