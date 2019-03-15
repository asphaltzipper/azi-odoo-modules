.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=====================
mrp_stock_reservation
=====================

This module was written to support the process of building parts kits for manufacturing orders.  It provides views where the user can see availability of a given product, along with a list of waiting stock moves (as a component of manufacturing orders).  Within the view, the user can scan the barcode of the manufacturing order and reserve the material for that order.  When scanning the barcode for another product, the form will reload, showing the new product scanned.

Installation
============

To install this module, you need to:

#. Clone the azi-odoo-modules repository on your Odoo server.

   * ``$ git clone https://github.com/asphaltzipper/azi-odoo-modules``

#. Add the new module repository to your Odoo configuration.

   * Append the new repository path to the *addons path* configuration
     variable.

      * e.g. ``addons_path = /opt/odoo/odoo/addons,/opt/odoo/azi-odoo-modules``
      * e.g. ``$ ./odoo-bin --addons-path="./addons,/opt/odoo/azi-odoo-modules"``

#. Restart Odoo.

#. Go to the menu *Apps > Apps* and search for "mrp_stock_reservation"

   * Install the *mrp_stock_reservation* module.

Usage
=====

Open a product form, and click the Mfg Reservations button.  Or, from the Mfg Work Import form, click the shopping cart button on the detail line.

While viewing the Mfg Reservations form, scan a product barcode to change to another product.  Or, scan a manufacturing order barcode to reserve material for that MO.

Known issues / Roadmap
======================

* No known issues

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/asphaltzipper/azi-odoo-modules/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed `feedback
<https://github.com/asphaltzipper/azi-odoo-modules/issues/new?body=module:%20
mrp_stock_reservation
%0Aversion:%209.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20
behavior**%0A%0A**Expected%20behavior**>`_.

Credits
=======

Contributors
------------

* Matt Taylor <mtaylor@asphaltzipper.com>

Funders
-------

The development of this module has been financially supported by:

* Asphalt Zipper, Inc.

Maintainer
----------

.. image:: http://asphaltzipper.com/img/elements/logo.png
   :alt: Asphalt Zipper, Inc.
   :target: http://asphaltzipper.com

This module is maintained by Asphalt Zipper, Inc.

To contribute to this module, please visit https://github.com/asphaltzipper/azi-odoo-modules.
