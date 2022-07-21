# Copyright 2017 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "azi_sale",
    "version": "12.0.1.0.0",
    "summary": "AZI Sales Customizations",
    "category": "Sales",
    "author": "Scott Saunders",
    "license": "AGPL-3",
    "website": "http://www.asphaltzipper.com",
    'description': """
AZI Specialized Customizations to Sales
=======================================

* Filter invoice and delivery addresses by partner on the sales order
* Add contractors and municipality filters to the crm team search view
* Improve customer warnings
* Prevent Children of Children
* Add priority to Contact Addresses
    """,
    "depends": [
        'sale',
        'crm',
        'sales_team_industry',
        'delivery',
        'sale_stock',
        'stock_available_unreserved',
    ],
    'data': [
        'views/crm_team_view.xml',
        'views/res_partner_views.xml',
        'views/sale_order_view.xml',
        'views/product_views.xml',
        'report/azi_sales_order.xml',
    ],
    "installable": True,
    "auto_install": False,
}
