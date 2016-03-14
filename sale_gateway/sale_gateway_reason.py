from datetime import datetime, timedelta
from openerp import SUPERUSER_ID
from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError
from openerp.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    reason_code = fields.Selection([
        ('gateway', 'Sales Gateway'),
        ('partofsale', 'Part Of Sale'),
        ('goodwill', 'Good Will'),
        ('customer_gateway', 'Customer Service Giveaway'),
        ('warrenty', 'Warrenty'),
    ], string='Reason Codes')

    @api.multi
    def _prepare_invoice_line(self, qty):
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        res.update({'reason_code': self.reason_code})
        return res

class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    reason_code = fields.Selection([
        ('gateway', 'Sales Gateway'),
        ('partofsale', 'Part Of Sale'),
        ('goodwill', 'Good Will'),
        ('customer_gateway', 'Customer Service Giveaway'),
        ('warrenty', 'Warrenty'),
    ], string='Reason Codes')