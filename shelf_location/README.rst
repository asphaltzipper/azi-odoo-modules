==============
Shelf Location
==============

* This module creates a shelf locations model that can be assigned many2many with products.  These are not stock.location type locations, and have no effect on stock transactions.  These shelf locations are similar to the X, Y, Z fields on the product (removed in v10).
* Create 2 reports related to `stock.shelf`
* Inherit "Transfer Slip" report to display "Shelf Locations".

Installation
============
* No specific installation required.

Configuration
=============
* No specific configuration required.

Usage
=====
* Stock Shelf: Inventory > Master Data > Stock Shelf
* Adding Shelf Location from Product: Inventory > Master Data > Products > Inventory
* Transfer Slip Report: Inventory > Reporting > Stock Moves
* AZI Location Labels report: Inventory > Master Data > Stock Shelf
* Product Listing report: Inventory > Master Data > Stock Shelf