def migrate(env, version):
    if not version:
        return

    env.execute("""DELETE FROM public.ir_asset 
                WHERE path in ('/web_responsive/static/src/js/web_responsive.js','/web_responsive/static/src/css/web_responsive.scss')
 
""")
