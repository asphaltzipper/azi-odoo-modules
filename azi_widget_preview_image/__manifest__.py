# -*- coding: utf-8 -*-
################################################################################
#
#    Original Module:
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023 Cybrosys Technologies
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    Modified Version:
#    Copyright (C) 2025 John Welch/ Asphalt Zipper
#    Author: John Welch
#
#    This is a derivative work based on the original Cybrosys module.
#    It is distributed under the terms of the GNU AFFERO GENERAL PUBLIC LICENSE
#    Version 3 (AGPL-3).
#
################################################################################
# (c) 2025 John Welch

{
    "name": "AZI Widget Preview Image",
    "version": "16.0.1.0.0",
    "summary": "Image Preview",
    "category": "Extra Tools",
    "author": "John Welch",
    "license": "AGPL-3",
    "website": "http://www.github.com/asphaltzipper",
    'description': """
        Preview image when click on it.
    """,
    "depends": [
        "web"
    ],
    "assets": {
        "web.assets_backend": {
            "azi_widget_preview_image/static/src/js/image_preview_widget.js",
            "azi_widget_preview_image/static/src/xml/widget_image_preview.xml",
        }
    },
    "installable": True,
    "auto_install": False,
}
