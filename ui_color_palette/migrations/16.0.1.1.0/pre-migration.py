def migrate(env, version):
    if not version:
        return
    env.execute("""
        DELETE FROM ir_asset 
        WHERE path in ('/ui_color_palette/static/src/scss/variables.scss', '/ui_color_palette/static/src/scss/ui.scss' )
    """)
