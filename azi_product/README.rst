.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

AZI Product
===========
* Added fields in `product.template`, `product.product`, `uom.category` and `uom.uom`
* Added `sql_constraints` for unit of measure and unit of measure category to force a unique name
* Changed the display of attribute values to be shown like (attribute.name : value.name) when selecting Attribute Values
* Override the duplicate/copy in `uom.uom` and `uom.category` to add "(copy)" after name to ensure unique name.

Installation
============
* No specific installation required.

Configuration
=============
* No specific configuration required.

Usage
=====
* Inventory > Master Data > Products > Added new product manager option and enlarged new image size for the product
* Inventory > Configuration > Settings > Products > (enable) Unit of measure