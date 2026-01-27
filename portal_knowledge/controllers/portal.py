from odoo import http, _
from odoo.http import request
from odoo.exceptions import AccessError, MissingError
from odoo.addons.portal.controllers.portal import CustomerPortal, pager


class DocumentPagePortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'knowledge_count' in counters:
            document_page = request.env['document.page']
            values['knowledge_count'] = 0
            if document_page.check_access_rights('read', raise_exception=False):
                values['knowledge_count'] = document_page.search_count([('type', '=', 'content')])
        return values

    def _prepare_knowledge_values(self, page=1, **kwargs):
        document = request.env['document.page']
        url = '/my/knowledge'
        values = self._prepare_portal_layout_values()
        sortby = 'name'
        searchbar_sortings = {'name': {'label': 'Knowledge Articles', 'order': 'name'}}

        if not document.check_access_rights('read', raise_exception=False):
             return values

        # Pager logic
        domain = [('type', '=', 'content')]
        # Count for pager
        count = document.search_count(domain)

        pager_values = pager(
            url=url,
            total=count,
            page=page,
            step=self._items_per_page,
        )
        documents = document.search(domain, limit=self._items_per_page,
                                    offset=pager_values['offset'])

        values.update({
            'documents': documents.sudo(),
            'page_name': 'knowledge',
            'pager': pager_values,
            'default_url': url,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return values

    @http.route(['/my/knowledge', '/my/knowledge/page/<int:page>'], type='http', auth='user', website=True)
    def portal_knowledge_articles(self, **kwargs):
        values = self._prepare_knowledge_values(**kwargs)
        return request.render('portal_knowledge.portal_knowledge', values)

    @http.route(['/my/knowledge/<int:document_id>'], type='http', auth="user", website=True)
    def portal_knowledge_article_page(self, document_id, access_token=None, **kwargs):
        try:
            document_sudo = self._document_check_access('document.page', document_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = {
            'document': document_sudo,
        }

        # _get_page_view_values is often used for breadcrumbs and history
        values = self._get_page_view_values(
            document_sudo, access_token, values, 'my_knowledge_history', False)

        return request.render('portal_knowledge.knowledge_content_portal_template', values)
