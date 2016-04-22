.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

==========================================
Manufacturing Orders as Independent Demand
==========================================

This module makes the following changes:
* Create computed field independent_mts on the Manufacturing Order
* Provide filters for managing these MOs
* Provide list actions for confirming, cancelling, and deleting MOs
* Allow user to connect SO Lines to MOs by choosing a destination stock move (presumably representing a sales order line delivery)

The independent_mts field marks an MO as independent demand.  This is used to provide the user with master schedule functionality.  All of the ID MOs will need to be confirmed in order to create dependent demand (stock moves) for the components.  Changes to the schedule require the ID MOs to be canceled and deleted.

The list actions allow the user to manage Independent MTS demand in batches.

Independent demand is implied when an MO is associated with an SO, or when the MO is NOT associated with a procurement order.

Usage
=====

* Go to Manufacturing > Manufacturing > Manufacturing Orders
* Edit an existing MO and fill in the Independent MTS field
* Confirm the MO
* Executing Run Schedulers will generate orders for the dependent demand on the MOs (raw materials)

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
