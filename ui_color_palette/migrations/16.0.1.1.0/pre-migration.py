from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    if not version:
        return
    cr.execute("""
        DELETE FROM ir_asset
        WHERE path in ('/ui_color_palette/static/src/scss/variables.scss',
                       '/ui_color_palette/static/src/scss/ui.scss')
    """)
