
from openerp.osv import fields, osv, expression

class account_account_type(osv.osv):
    _inherit = "account.account.type"

    _columns = {
        'active': fields.boolean('Active'),
        'account_ids': fields.one2many('account.account', 'user_type', 'Accounts'),
    }

    _defaults = {
        'active': True,
    }

