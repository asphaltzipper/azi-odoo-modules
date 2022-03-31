{
    "name": "Stock Request Schedule",
    "version": "12.0.1.0.0",
    "summary": "Stock Request Schedule",
    "category": "Stock",
    "author": "Matt Taylor",
    "website": "http://www.github.com/asphaltzipper",
    'description': """
Stock Request Schedule
======================
This module provides views and tools for managing stock requests like items in
a master production schedule.
    """,
    'depends': [
        'stock_request',
        'stock_request_submit',
        'stock_request_mrp',
        'sale',
        'azi_mrp',
        'configurator_management',
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/product_views.xml',
        'views/stock_request_views.xml',
        'views/sale_order_views.xml',
        'wizard/change_stock_request_views.xml',
        'report/managing_independent_demand_views.xml',
        'views/stock_templates.xml',
        'report/schedule_sale_order_report.xml',
        'report/schedule_sale_order_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}
