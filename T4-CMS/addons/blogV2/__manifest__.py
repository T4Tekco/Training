# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": "Blog",
    'version': '1.0.1',
    "category": "Accounting/Payment Providers",
    "sequence": 0,
    "summary": "A Vietnam payment provider.",
    "description": "Module for managing blog transfers, scheduling blog posts, and server configurations for blog management in Odoo.",  # Added description text
    "author": "",  # You can fill in the author name here if needed
    "depends": [
        "base", 
        "web", 
        "website_blog"
    ],
    "data": [  # Do not change the order
        "security/ir.model.access.csv",
        "data/cron_job_transfer.xml",
        "views/blog_transfer_scheduler.xml",
        "views/blog_transfer.xml",
        "views/serverView.xml",
        "views/menuItems.xml",
        "views/blog_transfer_kanban.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
    "license": "LGPL-3",

    'assets': {
        'web.assets_backend': [
            'blogV2/static/src/js/*.js',
            'blogV2/static/src/xml/*.xml',
        ]
    }
}
