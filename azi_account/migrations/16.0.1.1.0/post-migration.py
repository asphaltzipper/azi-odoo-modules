def migrate(env, version):
    if not version:
        return
    env.execute("""
        DELETE FROM ir_ui_view
        WHERE name in ('account.invoice.so.reference', 'bank.statement.line.form.glentry')
        and arch_fs = 'azi_account/views/account_view_changes.xml'
    """)

