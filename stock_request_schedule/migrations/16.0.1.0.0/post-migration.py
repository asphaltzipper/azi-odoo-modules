def migrate(env, version):
    if not version:
        return
    env.execute("""
        DELETE FROM ir_asset 
        WHERE path = '/stock_request_schedule/static/src/js/schedule_sale_order.js'
    """)
