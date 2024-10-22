from odoo import _, models, fields, api
from odoo.exceptions import ValidationError


class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    code = fields.Char(
        string='Code',
        help='Short descriptive code to be concatenated into a variant code',
    )
    no_bom_component = fields.Boolean(
        string="No Component",
        required=True,
        default=False,
        copy=False,
        help="This attribute value will not add a component to the template Bill of "
             "Materials",
    )
    product_qty = fields.Float(
        string="Product Qty",
    )

    @api.constrains("product_id", "no_bom_component")
    def _validate_no_bom_component(self):
        for value in self:
            if value.no_bom_component and value.product_id:
                raise ValidationError(_(
                    "Assigning a product and setting the No Component flag are "
                    "mutually exclusive: %s/%s",
                    value.attribute_id.name,
                    value.name,
                ))

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
