# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": "Blog Transfer",
    "version": "1.0",
    "category": "Blog Transfer",
    "sequence": 0,
    "summary": "Blog Transfer.",
    "description": " ",
    "author": "",
    "depends": ["base", "web", "website_blog"],
    "data": [  
        "security/ir.model.access.csv",
        "data/cron_check_blog_transfer.xml",
        "views/blog_transfer_scheduler.xml",
        "views/blog_transfer.xml",
        "views/blog_transfer_scheduler.xml",
        "views/blog_transfer.xml",
        "views/blog_transfer_serverView.xml",
        "views/blog_transfer_menuItems.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
    "license": "LGPL-3",

    'assets': {
        'web.assets_backend':
        [
            'Blogtransfer/static/src/js/*.js',
            'Blogtransfer/static/src/xml/*.xml',
        ]
    }

}
