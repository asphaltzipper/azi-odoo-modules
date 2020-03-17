MFG Integration
===============
* Create two new work centers and routings and link routing to the work center
* Add a new field that displays the code of the work center in Routing
* Create a new model for MFG work Batch in which you can import products and then it will create manufacturing order
* Add new fields in Bill of materials and modify the tree view
* Create a wizard that imports csv file that contains data of MFG Work Batch
* Create a wizard that changes actual quantity of products in MFG Work Batch and sheet value
* Add a new field that displays the code of the work center in Manufacturing Order in the tree and search view
* Add new fields related to manufacturing in `product.template`
* Add a new field in the Unit of Measure Category
* Add a priority field that is calculated in Work Orders
* Create a new model for Raw Material
* Create a new model for Raw Material Thickness
* Create a new wizard to create Bill of Materials to `product.template`
* Create a wizard that import multi radan files and create for them MFG Work Batch

Installation
============
* No specific installation required.

Configuration
=============
* Enable Units of Measure: Inventory > Configuration > Settings

Usage
=====
* (Laser and Brake) Work Center: Manufacturing > Master Data > Work Centers
* (laser_template and laser_brake_template) Routings: Manufacturing >Master Data > Routings
* Routing (newly added field): Manufacturing > Master Data > Routings > Check tree view
* MFG Work Batch: Manufacturing > Operations
* Bill of Materials: Manufacturing > Master Data
* Import CSV: Manufacturing > Operations > MFG Work Batch > Open form view > Click on "Import Work" button
* Multiply Sheets: Manufacturing > Operations > MFG Work Batch > Create a record then set state to be "imported" > Click on "Change" button beside "Sheet" field
* Manufacturing Order (newly added field): Manufacturing > Operations > Check tree view
* Products (newly added fields): Manufacturing > Master Data > Products > open a product > MFG page
* UOM Category: Inventory > Configuration > Unit of Measures > UoM Categories > open form view
* Work Orders (newly added field): Manufacturing > Operations > Work Orders > open form view
* Raw Material: Inventory > Configuration > Products
* Raw Material Thickness: Inventory > Configuration > Products
* Create BOM Wizard: Manufacturing > Master Data > Products > open a product > MFG page > below MFG Code
* Import Radan DRG: Manufacturing > Operations