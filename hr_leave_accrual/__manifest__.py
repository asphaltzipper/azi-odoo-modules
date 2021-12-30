# Copyright (C) 2021 Asphalt Zipper, Inc.
# Author Matt Taylor


{
    "name": "hr_leave_accrual",
    "version": "12.0.1.0.0",
    "summary": "Employee Leave Accrual",
    'category': 'Human Resources',
    "author": "Matt Taylor",
    "website": "http://www.asphaltzipper.com",
    'description': """
Employee Leave Accrual
======================

* Policy
* User-Policy assignments
* Leave type
* Leave Allocation
    """,
    "depends": [
        'hr',
        'report_xlsx',
    ],
    'data': [
        'demo/leave_type.xml',
        'demo/leave_accrual_policy.xml',
        'security/leave_accrual_security.xml',
        'security/ir.model.access.csv',
        'views/leave_accrual_views.xml',
        'views/hr_employee_views.xml',
        'reports/leave_allocations_yearly_report.xml',
        'wizards/wizard_generate_accruals_views.xml',
        'wizards/wizard_leave_allocations_yearly_report.xml',
    ],
    'demo': [
        'demo/leave_type.xml',
        'demo/leave_accrual_policy.xml',
    ],
    "installable": True,
    "auto_install": False,
}
