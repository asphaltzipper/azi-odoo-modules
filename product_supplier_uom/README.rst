.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

==============================================
Varying Units of Measure for Product Suppliers
==============================================

This module makes the following changes:
* Make product_uom field on product suppliers independent of the uom_po_id field on product template
* Set the default uom for new suppliers equal to the uom_po_id field from product template
* Add uom_ref_id field on product.supplierinfo as a related field to the uom_id field on product template
* Enforce uom category consistency against uom_ref_id
* Show Purchase UOM field (product_uom) on product.supplierinfo view
* Set a domain to only show UOMs from the same category as uom_ref_id
* TODO: Change all other code from using uom_po_id field to use the get_purchase_uom() method

Usage
=====

* Go to Inventory > Products
* Edit an existing Product go to Inventory Tab
* Add a vendor
* Choose a Purchase UOM

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
