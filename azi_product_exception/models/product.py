from odoo import models, fields, api, _
from odoo.addons.base.models.res_partner import WARNING_MESSAGE, WARNING_HELP


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    receipt_line_warn = fields.Selection(WARNING_MESSAGE, 'Receipt Line', help=WARNING_HELP, required=True,
                                         default="no-message")
    receipt_line_warn_msg = fields.Text('Message for Receipt Line')
