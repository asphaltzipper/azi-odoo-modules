# (c) 2026 John Welch

{
    "name": "Ollama Connector",
    "version": "16.0.1.0.0",
    "summary": "AI, Ollama",
    "category": "Tools",
    "author": "John Welch",
    "license": "AGPL-3",
    "website": "http://www.github.com/asphaltzipper",
    'description': """
        Create an Ollama connector 
    """,
    "depends": [
        "base",
        "mail",
    ],
    "external_dependencies": {"python": ["ollama"]},
    "data": [
        'security/ir.model.access.csv',
        'views/ollama_connector_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}
