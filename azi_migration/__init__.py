def post_init_hook(cr, registry):
    cr.execute("""
        UPDATE ir_module_module 
        SET state = 'to remove' 
        WHERE name in (
            'product_quality', 'azi_web', 'account_tweaks', 'web_drag_drop_attach', 'mrp_production_merge', 'web_responsive') and state = 'installed'
    """)
