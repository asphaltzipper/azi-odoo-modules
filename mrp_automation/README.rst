.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

==============
MRP Automation
==============
* Create a Manufacturing Order by scanning a production kit barcode
* Produce a Manufacturing Order (i.e. launch and fill the produce wizard) by scanning the MO barcode


Installation
============
* No specific installation instructions

Configuration
=============
* No configuration settings

Usage
=====
Steps for creating and processing a manufacturing order:

#. Click Manufacturing -> Operations -> MO Automation
#. Scan a kit barcode (this will create a Manufacturing Order)
#. Print the resulting MO
#. Click Manufacturing -> Operations -> MO Automation
#. Scan the MO barcode
#. Scan an employee badge
#. Specify the number of labor hours for the employee on this MO
#. Click RECORD PRODUCTION

Known issues / Roadmap
======================
* None

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/asphaltzipper/azi-odoo-modules/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed `feedback
<https://github.com/asphaltzipper/azi-odoo-modules/issues/new?body=module:%20
mrp_planned_pick_kit
%0Aversion:%209.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20
behavior**%0A%0A**Expected%20behavior**>`_.

Credits
=======

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
