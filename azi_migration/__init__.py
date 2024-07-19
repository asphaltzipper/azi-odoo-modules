def pre_init_hook(cr):
    cr.execute("""DELETE FROM public.ir_asset 
                    WHERE path in ('/web_responsive/static/src/js/web_responsive.js','/web_responsive/static/src/css/web_responsive.scss')

    """)
    cr.execute("""
        UPDATE ir_module_module 
        SET state = 'to remove' 
        WHERE name in (
            'product_quality', 'azi_web', 'account_tweaks', 'web_drag_drop_attach', 
            'mrp_production_merge', 'document_multi_upload', 'owncloud_odoo', 
            'cloud_base', 'ywt_odoo_taxjar_connector', 'web_responsive'
        ) and state = 'installed'
    """)
