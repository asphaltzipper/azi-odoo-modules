# (c) 2025 John Welch

{
    "name": "Unit Telemetry",
    "version": "16.0.1.0.0",
    "summary": "IOT, Lot",
    "category": "Field Service",
    "author": "John Welch",
    "license": "AGPL-3",
    "website": "http://www.github.com/asphaltzipper",
    "description": """
        Display serial numbers and other details for portal users
    """,
    "depends": [
        'stock',
        'mqtt_integration',
        'mail',
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/mqtt_client_views.xml',
        'views/mqtt_topic_views.xml',
        'wizards/mqtt_process_message_views.xml',
        'views/mqtt_message_history_views.xml',
        'views/res_config_settings_views.xml',
        'views/stock_lot_views.xml',
        'views/unit_telemetry_views.xml',
        'data/unit_telemetry_data.xml',
        'data/ir_cron_data.xml',
    ],
    "installable": True,
    "auto_install": False,
}
