def migrate(env, version):
    if not version:
        return
    env.execute("""
        DELETE FROM ir_asset WHERE path = '/mrp_automation/static/src/js/mo_barcode_handler.js'
    """)
