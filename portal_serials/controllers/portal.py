import base64
from odoo import http, _
from odoo.http import request
from odoo.exceptions import AccessError, MissingError
from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import pager


class CustomerPortal(portal.CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        stock_lot = request.env['stock.lot']

        if 'serial_count' in counters:
            values['serial_count'] = partner.parent_id.serial_count \
                if stock_lot.check_access_rights('read', raise_exception=False) else 0
        return values

    def _prepare_serial_values(self, page=1, **kwargs):
        stock_lot = request.env['stock.lot']
        partner = request.env.user.partner_id.parent_id
        url = '/my/serials'
        values = self._prepare_portal_layout_values()
        sortby = 'name'
        searchbar_sortings = {'name': {'label': 'Serial/Lot', 'order': 'name'}}

        pager_values = pager(
            url=url,
            total=partner.serial_count,
            page=page,
            step=self._items_per_page,
        )
        serial_numbers = stock_lot.search([('partner_id', '=', partner.id)], limit=self._items_per_page, offset=pager_values['offset'])

        values.update({
            'serials': serial_numbers.sudo(),
            'page_name': 'serial',
            'pager': pager_values,
            'default_url': url,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })

        return values

    @http.route(['/my/serials', '/my/serials/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_serial_numbers(self, **kwargs):
        values = self._prepare_serial_values(**kwargs)
        return request.render("portal_serials.portal_my_serials", values)

    @http.route(['/my/serials/<int:serial_id>'], type='http', auth="user", website=True)
    def portal_serial_page(self, serial_id, access_token=None, **kwargs):
        try:
            serial_sudo = self._document_check_access('stock.lot', serial_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = {
            'serial': serial_sudo,
            'res_company': serial_sudo.company_id,
        }

        values = self._get_page_view_values(
            serial_sudo, access_token, values, 'my_serial_history', False)

        return request.render('portal_serials.serial_portal_template', values)

    @http.route(['/my/serials/download/<int:document_id>'], type='http', auth='user', website=True)
    def preview_document(self, document_id, **kw):
        attachment = request.env['ir.attachment'].sudo().browse(document_id)
        if not attachment.exists() or attachment.res_model != 'stock.lot':
            return request.not_found()
        partner = request.env.user.partner_id.parent_id
        lot = request.env['stock.lot'].browse([int(attachment.res_id)])
        if lot.partner_id.id != partner.id:
            return request.not_found()
        filecontent = base64.b64decode(attachment.datas)
        return request.make_response(
            filecontent,
            headers=[
                ('Content-Type', attachment.mimetype or 'application/octet-stream'),
                ('Content-Disposition', f'inline; filename="{attachment.name}"'),
            ]
        )

