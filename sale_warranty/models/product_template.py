from odoo import models, fields, api, _


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_warranty = fields.Boolean(
        string='Is Warranty',
        default=False,
        required=True,
        help="This product is a warranty",
    )
    warranty_units = fields.Selection(
        selection=[('day', 'Days'), ('month', 'Months'), ('year', 'Years')],
        string='Warranty Units',
    )
    warranty_duration = fields.Integer(
        string='Warranty Duration',
    )
