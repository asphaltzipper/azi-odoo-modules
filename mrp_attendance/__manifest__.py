# (c) 2025 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "MRP Attendance",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "summary": "Use attendance data with MRP productivity data",
    "category": "Manufacturing",
    "author": "Matt Taylor",
    "website": "http://www.github.com/asphaltzipper",
    'description': """
MRP Attendance
==============

* Reports for comparing workorder time with employee attendance
""",
    "depends": [
        "mrp",
        "hr_attendance",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_employee_views.xml",
        "views/mrp_attendance_compare_views.xml",
    ],
    "installable": True,
    "auto_install": False,
}
