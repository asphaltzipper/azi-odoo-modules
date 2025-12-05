# (c) 2025 John Welch

{
    "name": "AZI IOT MQTT",
    "version": "16.0.1.0.0",
    "summary": "IOT, Lot",
    "category": "Inventory",
    "author": "John Welch",
    "license": "AGPL-3",
    "website": "http://www.github.com/asphaltzipper",
    "description": """
        Display serial numbers and other details for portal users
    """,
    "depends": [
        'serial_crm',
        'mqtt_integration',
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/mqtt_client_views.xml',
        'views/mqtt_topic_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}
