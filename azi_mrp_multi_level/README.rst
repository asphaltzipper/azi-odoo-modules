AZI MRP Multi Repair
====================
* Create a `material.plan.log` model to create a new log for running multi mrp level
* Add new fields in `mrp.inventory` and modify views
* Add new fields in `mrp.planned.order` and modify views
* Link `mrp.move` with `stock.request`
* Modify `product.mrp.area` by removing groups from form view
* Modify `mrp.multi.level` to add log in `material.plan.log`, also run wizard in background

Installation
============
* No specific installation required.

Configuration
=============
* No specific configuration required.

Usage
=====
* Material Plan Log: Manufacturing > Reporting > Material Plan Log
* MRP Inventory: Manufacturing > Operations > MRP Inventory
* Planned Orders: Manufacturing > Planning > Planned Orders
* MRP Area: Manufacturing > Master Data > Product MRP Area Parameters
* MRP Multi Level: Manufacturing > Operations > Run MRP Multi Level