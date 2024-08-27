import logging

_logger = logging.getLogger(__name__)


def pre_init_hook(cr):
    _logger.info("Delete records from ir_asset")
    cr.execute("""
        DELETE FROM ir_asset 
        WHERE path in ('/document_multi_upload/static/src/css/document_multi_upload.scss',
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
                       '/azi_web/static/src/scss/primary_variables.scss',
                       '/azi_web/static/src/scss/form_view.scss',
                       '/mrp_automation/static/src/js/mo_barcode_handler.js',
                       '/stock_request_schedule/static/src/js/schedule_sale_order.js',
                       '/ui_color_palette/static/src/scss/variables.scss',
                       '/ui_color_palette/static/src/scss/ui.scss',
                       '/serial_crm/static/src/js/combined_bom_report.js',
                       '/azi_account/static/src/js/azi_account_assets.js',
                       '/azi_mrp/static/src/js/mrp_bom_report.js', 
                       '/azi_mrp/static/src/js/product_bom_report.js'
                       
        )
    """)
    _logger.info("Delete records from ir_ui_view")
    cr.execute("""
            DELETE FROM ir_ui_view
            WHERE name = 'report_invoice_document_inherit'
            and arch_fs = 'azi_account/report/report_invoice.xml'
        """)

    cr.execute("""
                DELETE FROM ir_ui_view
                WHERE name in ('account.invoice.so.reference', 'bank.statement.line.form.glentry')
                and arch_fs = 'azi_account/views/account_view_changes.xml'
            """)
