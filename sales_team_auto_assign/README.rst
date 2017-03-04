.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

======================
sales_team_auto_assign
======================

This module was written to extend the functionality of *Sales Teams*, *Sales
Team Industries* and *Sales Regions* to allow you to auto-assign *Sales Teams*
to a *Customer* based on *Sales Regions* and *Industries*.

Auto-assignment does not require an *Industry* to be assigned.


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
#. Go to the menu *Apps > Apps* and search for "sales_team_auto_assign"
   * Install the *sales_team_auto_assign* module.

Usage
=====

New *Customers* are automatically assigned to *Sales Team(s)* given a *State*
and *Industry* (Industry is optional).

For existing customers, you need to:

#. Go to the menu *Sales > Configuration > Re-assign Sales Teams* and run.

 * For more information on *Region Team Types* and *Sales Team Regions* see the
   `sales_team_region
   <https://github.com/asphaltzipper/azi-odoo-modules/tree/master/sales_team_region>`_
   module.
 * To create and categorically assign *Industries* to *Sales Teams* and
   *Customers* see the `sales_team_industry
   <https://github.com/asphaltzipper/azi-odoo-modules/tree/master/sales_team_industry>`_
   module.

Known issues / Roadmap
======================

* No known issues

Possible `related issues
<https://github.com/asphaltzipper/azi-odoo-modules/issues?utf8=%E2%9C%93&q=is%3Aissue%20is%3Aopen%20
sales_team_auto_assign
%20>`_.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/asphaltzipper/azi-odoo-modules/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed `feedback
<https://github.com/asphaltzipper/azi-odoo-modules/issues/new?body=module:%20
sales_team_auto_assign
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
