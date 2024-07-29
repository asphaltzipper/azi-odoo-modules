def migrate(env, version):
    if not version:
        return
    env.execute("""
        DELETE FROM ir_ui_view
        WHERE name = 'report_invoice_document_inherit'
        and arch_fs = 'azi_account/report/report_invoice.xml'
    """)

