def migrate(env, version):
    if not version:
        return
    env.execute("""
        DELETE FROM public.ir_asset 
        WHERE path in ('/azi_mrp/static/src/js/mrp_bom_report.js', '/azi_mrp/static/src/js/product_bom_report.js')
    """)

