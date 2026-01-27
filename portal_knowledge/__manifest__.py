{
    "name": "Portal Knowledge",
    "version": "16.0.1.0.0",
    "summary": "Portal access for Document Page Knowledge Base",
    "category": "Knowledge",
    "author": "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/knowledge",
    "license": "AGPL-3",
    "depends": [
        "document_page",
        "document_page_approval",
        "portal",
    ],
    "data": [
        "views/document_page_portal_templates.xml",
        'views/breadcrumbs_templates.xml',
        "security/ir.model.access.csv",
    ],
    "assets": {
        "web.assets_frontend": [
            "portal_knowledge/static/src/js/portal_knowledge.js",
        ],
    },
    "installable": True,
}
