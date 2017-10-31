# -*- coding: utf-8 -*-
# Copyright (C) 2014 Therp BV (<http://therp.nl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

# commit 020657d5ce5785e44ca64829fb3f96c7b56fbfb2
# Author: Frédéric Garbely <BT-fgarbely@users.noreply.github.com>
# Date:   Thu Feb 2 19:16:24 2017 +0100
# https://github.com/OCA/web/tree/10.0

{
    "name": "Show sheets with full width",
    "version": "10.0.1.0.1",
    "author": "Therp BV,Sudokeys,GRAP,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "summary": "Use the whole available screen width when displaying sheets",
    "category": "Tools",
    "depends": [
        'web',
    ],
    "data": [
        "view/qweb.xml",
    ],
    "installable": True,
}
