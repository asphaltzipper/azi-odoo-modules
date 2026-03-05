# (c) 2026 John Welch

{
    "name": "OpenAI Connector",
    "version": "16.0.1.0.0",
    "summary": "AI, OpenAI",
    "category": "Tools",
    "author": "John Welch",
    "license": "AGPL-3",
    "website": "http://www.github.com/asphaltzipper",
    'description': """
        Create an OpenAI connector 
    """,
    "depends": [
        "base",
        "mail",
    ],
    "external_dependencies": {"python": ["openai", "python-dotenv"]},
    "data": [
        'security/ir.model.access.csv',
        'views/openai_connector_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}
