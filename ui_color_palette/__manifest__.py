# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'license': 'LGPL-3',
    "name": "Custom Color Palette",
    "version": "16.0.1.0.0",
    "author": "Asphalt Zipper",
    "category": "Extra Tools",
    "summary": "Change Odoo color palette",
    'description': """
    This module migrated from v 10.0 that is written by Bista Solutions to v 16.0 by Asphalt Zipper
    For Odoo Enterprise Version 16.0, this module replaces the default Odoo purple color palette with a blue based 
    color palette. By editing the CSS and SCSS files in this module, you can further personalize Odoo with 
    your own color choices. This is a very simple module. 
    It serves as an ideal example for those who are learning how to build modules with Odoo.""",
    "website": "http://www.github.com/asphaltzipper",
    "depends": ["web_enterprise"],
    "assets": {
        'web._assets_primary_variables': [
            ('replace', 'web_enterprise/static/src/scss/primary_variables.scss', 'ui_color_palette/static/src/scss/variables.scss'),

        ],
        'web.assets_backend': [
            'ui_color_palette/static/src/css/color_change.css',
        ],
        'web.assets_common': [
            'ui_color_palette/static/src/scss/ui.scss'
        ],
    },
    "auto_install": False,
    "application": False,
    "installable": True,
}

