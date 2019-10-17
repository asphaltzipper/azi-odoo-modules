.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

===================================
Management Engineering Product Data
===================================

This module adds features to track and manage engineering related product attributes.  The Engineering department needs to attach data regarding versions, manufacturing, etc. to each product.

**Add new models:**

* Engineering categories
* Manufacturing part preparation
* Manufacturing part coating

**Add constraints and defaults:**

* Require Unique Product Code (product.default_code)
* Default value for default_code from eng_code sequence
* Constrain eng code format (using regular expression)
* Engineering management flag on product categories with regex to validate default_code

**Add product fields/attributes:**

* Product Manager
* Engineering management flag field
* Engineering Code, Revision, and Revision Delimiter fields
* Preparation and Coating fields
* Deprecated (obsolete) field
* "No-ECO Modification" field (Part changed with no ECO or revision)
* "Hold Production" field (A revision is impending, stop producing/purchasing this part)
* Engineering Category
* Engineering Notes

We also add fields for more friendly display of attachments:

* doc_ids
* version_doc_ids

We add a method for creating product versions.

Product Versions
================

On the product template form, we need a list of all products that are versions of the current product.
Do this as a computed one2many on product.template model.  For templates with multiple variants, no versions will be shown.  We won't create versions of products with multiple variants, only templates with one variant.

Configuration
=============

Create some engineering categories, coatings, and preparations.

On product categories, check the engineering management box, add a regex and revision delimiter.  Products in these categories will require an engineering category, and a valid default_code.

Usage
=====

To use this module, you need to:

#. Be a mechanical engineer

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
