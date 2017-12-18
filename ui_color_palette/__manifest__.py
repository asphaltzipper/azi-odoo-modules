# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# commit b3416b0fda3847c6bbf99c2c1ec21317a51e9df8
# Retrieved from github by cemigh on 2017-08-21:
# https://github.com/bistaray/odoo-apps#10.0

{
    'license': 'LGPL-3',
    "name" : "Custom Color Palette",
    "version" : "1.10.1",
    "author" : "Bista Solutions",
    "category" : "Extra Tools",
	"summary": "Change the Odoo color palette (Bista)",
    'description': "For Odoo Enterprise Version 10.0, this module replaces the default Odoo purple color palette with a blue based color palette. By editing the CSS and LESS files in this module, you can further personalize Odoo with your own color choices. This is a very simple module. It serves as an ideal example for those who are learning how to build modules with Odoo.",
    'maintainer': "Bista Solutions",
    'website': 'http://www.bistasolutions.com/odoo-implementation-partners',
    'images': ['static/description/banner.png'],
    "depends" : ["base"],
    "init_xml" : [],
    "demo_xml" : [],
        "data" : [
        'views/color_change.xml',
    ],
    "test" : [
    ],
    "auto_install": False,
    "application": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
