.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

===================
mrp_bom_effectivity
===================

This module extends the functionality of mrp_time_bucket to support BOM
effectivity dates and allow you to schedule against BOMs planned in the
future.

Usage
=====

* Set BOM validity dates
* Verify the correct BOM is selected for SO/PO/MO validation given the proper date in each case:
  * Sale Order (SO): Move Date (move.date)
  * Purchase Order (PO): Order Date (line.order_id.date_order) and Move Date (move.date)
  * Manufacturing Order (MO): Scheduled Date (production.date_planned)

Affected methods and when they are called:
* confirm sale for product w/BOM
  * mrp/stock:_action_explode
  * creates running outbound sales procurement
* run schedulers
  * for an mfg procurement
    * mrp/procurement:check_bom_exists
      * mrp/procurement:_prepare_mo_vals
      * mrp/mrp:_prepare_lines
  * creates running inbound mfg procurement
    * creates confirmed (ARM) MO
      * change qty
        * mrp/wizard/change_production_qty:change_prod_qty
        * mrp/mrp:_prepare_lines
      * reserve/force reservation
      * produce>confirm
  * creates running inbound purch procurement
    * creates draft PO
      * confirm order
        * purchase/purchase:_get_bom_delivered
        * purchase/purchase:_get_bom_delivered
        * mrp/stock:_action_explode
        * purchase/purchase:_get_bom_delivered
        * purchase/purchase:_get_bom_delivered
        * sets PO to purchase state
      * receive
      * (stock.picking) validate>apply
        * purchase/purchase:_get_bom_delivered
      * set to done
        * purchase/purchase:_get_bom_delivered
* (stock.picking) reserve/force availability (outgoing transfer)
  * validate
    * sale_mrp/sale_mrp:_get_delivered_qty

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/asphaltzipper/azi-odoo-modules/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed `feedback
<https://github.com/asphaltzipper/
azi-odoo-modules/issues/new?body=module:%20
mrp_bom_effectivity%0Aversion:%20
9.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Credits
=======

Contributors
------------

* Scott Saunders <ssaunders@asphaltzipper.com>

Maintainer
----------

.. image:: http://asphaltzipper.com/img/elements/logo.png
   :alt: Asphalt Zipper, Inc.
   :target: http://asphaltzipper.com

This module is maintained by Asphalt Zipper, Inc.

To contribute to this module, please visit https://github.com/asphaltzipper/azi-odoo-modules.
