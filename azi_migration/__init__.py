import logging

_logger = logging.getLogger(__name__)


def pre_init_hook(cr):
    _logger.info("Delete records from ir_asset")
    cr.execute("""
        DELETE FROM ir_asset 
        WHERE path in ('/web_responsive/static/src/js/web_responsive.js',
                       '/web_responsive/static/src/css/web_responsive.scss', 
                       '/document_multi_upload/static/src/css/document_multi_upload.scss',
                       '/document_multi_upload/static/src/js/document_multi_upload.js',
                       '/document_sidebar/static/src/js/document_sidebar.js',
                       '/web/static/src/scss/webclient.scss',
                       '/product_configurator/static/css/style.css',
                       '/report_xlsx/static/src/js/report/action_manager_report.js',
                       '/web_m2x_options/static/src/js/form.js',
                       '/web_listview_sticky_header/static/js/stick_headers.js',
                       '/web_notify/static/src/js/web_client.js',
                       '/web_search_with_and/static/src/js/search.js',
                       '/web_listview_sticky_header/static/lib/stickytableheaders/jquery.stickytableheaders.js',
                       '/product_configurator/static/js/relational_fields.js',
                       '/product_configurator/static/js/data_manager.js',
                       '/product_configurator/static/js/form_widgets.js',
                       '/base_report_to_printer/static/src/js/qweb_action_manager.js',    
                       '/web_drag_drop_attach/static/src/scss/drag_drop_attach.scss',    
                       '/web_drag_drop_attach/static/src/js/drag_drop_attach.js',    
        )
    """)
    _logger.info("Update unneeded modules to be uninstalled")
    cr.execute("""
        UPDATE ir_module_module 
        SET state = 'to remove' 
        WHERE name in (
            'product_quality', 'azi_web', 'account_tweaks', 'web_drag_drop_attach', 
            'mrp_production_merge', 'document_multi_upload', 'owncloud_odoo', 
            'cloud_base', 'ywt_odoo_taxjar_connector', 'web_responsive', 'document_sidebar'
        ) and state = 'installed'
    """)
