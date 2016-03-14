# -*- coding: utf-8 -*-

{
    'name': "Blanket Purchase Order",
    'summary': "Blanket Purchase Order.",
    'description': """
        Blanket Purchase Order not create a transfer when confirming the blanket PO
    """,
    'author': "Bista Solutions",
    'category': 'Usability',
    'version': '1.0',
    'depends': ['base','purchase', 'stock'],
    'data': [
        'wizard/request_release_wizard.xml',
        'blanket_purchase_order_view.xml'
    ],
    'installable': True,
    'application': True,
}
