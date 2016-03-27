.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

==========================================
Manufacturing Orders as Independent Demand
==========================================

This module creates a field on the Manufacturing Order form to flag an order as independent demand (make-to-stock).  This is used to instruct the scheduling algorithm to create dependent demand for components of the flagged MO.  Creating dependent demand for the components means creating "outbound" procurement orders.  An outbound procurement order is defined as one having destination (location_id) equal to the production location.

This module is only useful when combined with the functionality of mrp_procurement_only module.

Usage
=====

* Go to Manufacturing > Manufacturing > Manufacturing Orders
* Edit an existing MO and fill in the Independent MTS field
* Don't confirm the MO
* Executing Run Schedulers (from mrp_procurement_only) will generate procurement orders for the dependent demand on the MO (raw materials)

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/asphaltzipper/azi-odoo-modules/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/asphaltzipper/azi-odoo-modules/issues/new?body=module:%20mrp_production_note%0Aversion:%209.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Credits
=======

Contributors
------------

* Matt Taylor <mtaylor@asphaltzipper.com>

