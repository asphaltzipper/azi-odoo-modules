.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=================
sales_team_region
=================

This module extends the functionality of *Sales Teams* to support *Sales
Regions* with *Sales Region Team Types* which allow you to assign a *Region Team
Type* to a *Sales Region*, a *Sales Region* to a *Sales Team*, and *Sales
Team(s)* to a *Customer*.

*Sales Team Regions* may consist of *Country Groups*, *Countries*, and/or
*States*.

*Regions* are restricted from overlapping within the same *Sales Region Team
Type*.

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
#. Go to the menu *Apps > Apps* and search for "sales_team_region"
   * Install the *sales_team_region* module.

Configuration
=============

To configure this module, you need to:

#. Go to the menu *Sales > Configuration > Sales Region Types* and create
   multiple *Region Team Types* if you have multiple types of *Sales Teams* and
   need geographically overlapping *Regions*.
#. Go to the menu *Sales > Configuration > Sales Regions* and create one or
   more *Regions*. *Regions* can consist of *Country Groups*, *Countries* and/or
   *States*.

Usage
=====

To use this module, you need to:

#. Go to the menu *Sales > Configuration > Sales Teams* and assign a *Sales
   Region* to each *Sales Team*.
#. Go to the menu *Sales > Sales > Customers* and assign *Sales Team(s)* to
   *Customers*.

    * To create and categorically assign *Industries* to *Sales Teams* and
      *Customers* see the `sales_team_industry
      <https://github.com/asphaltzipper/azi-odoo-modules/tree/master/sales_team_industry>`_
      module.
    * For automatic assignment of *Sales Teams* to *Customers* see the
      `sales_team_auto_assign
      <https://github.com/asphaltzipper/azi-odoo-modules/tree/master/sales_team_auto_assign>`_
      module.

Known issues / Roadmap
======================

* If you want to move a region member (*Country Group*, *Country*, or *State*)
  from one region to another (within the same *Region Team Type*), you will
  either have to refresh the page **or** go to the top level menu in Odoo before
  going back into *Sales > Configuration > Sales Regions* in order for the
  member to be available for reassignment after removing it from the original
  region.

Possible `related issues
<https://github.com/asphaltzipper/azi-odoo-modules/issues?utf8=%E2%9C%93&q=is%3Aissue%20is%3Aopen%20
sales_team_region
%20>`_.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/asphaltzipper/azi-odoo-modules/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed `feedback
<https://github.com/asphaltzipper/azi-odoo-modules/issues/new?body=module:%20
sales_team_region
%0Aversion:%209.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20
behavior**%0A%0A**Expected%20behavior**>`_.

Credits
=======

Contributors
------------

* Scott Saunders <ssaunders@asphaltzipper.com>

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
