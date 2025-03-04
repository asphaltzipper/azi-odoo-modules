# Copyright 2025 Matt Taylor
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "SwipeClock Integration",
    "summary": "Import employee timeclock data from SwipeClock.",
    "version": "16.0.1.0.0",
    "development_status": "Beta",
    "author": "Matt Taylor",
    "website": "https://github.com/asphaltzipper/azi-odoo-modules",
    'category': 'Human Resources',
    "depends": ["hr_attendance"],
    "license": "AGPL-3",
    "data": [
        "views/hr_employee_views.xml",
        "views/hr_attendance_views.xml",
        "views/swipeclock_account_views.xml",
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
    ],
    'installable': True,
}
