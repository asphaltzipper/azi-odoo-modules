.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

================================
Simple Employee Leave Management
================================

This module adds features to track and manage employee leave.  Accruals are
usually generated once at the beginning of each year.  If an employee is added
during the year, the manager can generate accruals for a single employee.

Configuration
=============

Set up leave types and accrual policies.

Usage
=====

To use this module, you need to:

- Create leave types
  - e.g. Sick, Vacation
- Create accrual policies
  - e.g. One sick hour per one half-month period
- Assign policies to employees
  - Set the Start Date to the beginning of the year
  - Leave the End Date empty for open ended policies
- Generate accruals for a particular year
  - Leaves -> Operations -> Generate Accruals
- Generate yearly report and check ending balances
  - Leaves -> Reporting -> Generate Yearly Report

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/asphaltzipper/azi-odoo-modules/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Contributors
------------

* Matt Taylor <mtaylor@asphaltzipper.com>

Maintainer
----------

.. image:: http://asphaltzipper.com/img/elements/logo.png
   :alt: Asphalt Zipper, Inc.
   :target: http://asphaltzipper.com

This module is maintained by Asphalt Zipper, Inc.

To contribute to this module, please visit https://github.com/asphaltzipper/azi-odoo-modules.
