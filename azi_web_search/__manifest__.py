# -*- coding: utf-8 -*-
{
    "name": "AZI Web Search",
    "version": "16.0.1.0.0",
    "summary": "Search",
    "category": "web",
    "author": "John Welch",
    "license": "AGPL-3",
    "website": "http://www.github.com/asphaltzipper",
    'description': """
AZI Web Search
==============
* Modify Search to use and operator by default
    """,
    'depends': [
        'web',
    ],
    "assets": {
        "web.assets_backend": [
            "/azi_web_search/static/src/js/search_model.js",
            "/azi_web_search/static/src/js/search_bar.js",
        ],
    },
    "installable": True,
    "auto_install": False,
}
