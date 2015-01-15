from openerp.osv import osv, fields

class res_partner(osv.osv):

    _inherit = "res.partner"

    _columns = {
        'county_id': fields.many2one("res.country.state.county", 'County'),
    }

    def _address_fields(self, cr, uid, context=None):
        address_fields = set(super(res_partner, self)._address_fields(cr, uid, context=context))
        address_fields.add('county_id')
        return list(address_fields)
