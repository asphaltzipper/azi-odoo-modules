# -*- coding: utf-8 -*-

from openerp.osv import fields,osv
from openerp.tools.translate import _

class res_partner(osv.osv):
    _inherit = 'res.partner'

    _columns = {
        # select=True creates database index (searchable)
        'code': fields.char('Code', select=True),
    }

    # set unique case sensitive constraint on the database field
    _sql_constraints = [
        ('code_unique', 'unique(code)', \
        'A record with the same code already exists [code_unique]')
    ]

#    def _check_unique_insensitive(self, cr, uid, ids, context=None):
#        sr_ids = self.search(cr, 1 , [], context=context)
#        lst = [x.name.upper() for x in self.browse(cr, uid, \
#        sr_ids, context=context) if x.name and x.id not in ids]
#        for self_obj in self.browse(cr, uid, ids, context=context):
#            if self_obj.name and self_obj.name.upper() in lst:
#                return False
#            return True
#
#    # set addtl. constraint to ensure case insensitive uniqueness
#    _constraints = [(_check_unique_insensitive, \
#        'A record with the same code already exists [_check_unique_insensitive]', ['code'])]
#
#    # set unique insensitive constraint on the database field
#    _sql = """DROP INDEX IF EXISTS res_partner_code_index_uniq;
#            CREATE UNIQUE INDEX
#            res_partner_code_index_uniq ON res_partner (upper(code))
#    """
#
#    # execute SQL code provided by _sql
#    def _auto_init(self, cr, context=None):
#        ret = super(res_partner, self)._auto_init(cr, context)
#        self._execute_sql(cr)
#        return ret

    # force uppercase for code field in view (res.partner.form)
    def onchange_case(self, cr, uid, ids, code):
        return {'value': {'code': str(code).replace(' ','').upper()}} \
        if code else {'value': {'code': ''}}

    # force uppercase for code field on res_partner record create
    def create(self, cr, uid, vals, context=None):
        if 'code' in vals:
                vals['code'] = vals['code'].replace(' ','').upper()
        return super(res_partner, self).create(cr, uid, vals, context)

    # force uppercase for code field on res_partner record write
    def write(self, cr, uid, ids, vals, context=None):
        if 'code' in vals:
                vals['code'] = vals['code'].replace(' ','').upper()
        return super(res_partner, self).write(cr, uid, ids, vals, context)

    # on copy, append the partner code to maintain uniqueness
    def copy(self, cr, uid, id, default=None, context=None):
        if context is None:
            context={}
        product = self.read(cr, uid, id, ['code'], context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = product['code'] + _('(COPY)')
        return super(res_partner, self).copy(cr, uid, id, default=default, context=context)

res_partner()
