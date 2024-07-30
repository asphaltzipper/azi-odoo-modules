import logging

_logger = logging.getLogger(__name__)


def migrate(env, version):
    if not version:
        return
    _logger.info("Delete ir_asset record")
    env.execute("DELETE FROM ir_asset WHERE path = '/azi_account/static/src/js/azi_account_assets.js'")
    _logger.info("Deleted `report_invoice_document_inherit` from ir_ui_view")
    env.execute("""
        DELETE FROM ir_ui_view
        WHERE name = 'report_invoice_document_inherit'
        and arch_fs = 'azi_account/report/report_invoice.xml'
    """)
    _logger.info("Delete records from ir_ui_view")
    env.execute("""
            DELETE FROM ir_ui_view
            WHERE name in ('account.invoice.so.reference', 'bank.statement.line.form.glentry')
            and arch_fs = 'azi_account/views/account_view_changes.xml'
        """)

