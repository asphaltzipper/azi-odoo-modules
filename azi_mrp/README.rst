AZI MRP
=======
* Modify "Bill of Materials" to connect attachments to `ir.attachment` instead of `mrp.document`
* Create new reports for "AZI Production Order" and "Production Picking"
* Create new report that print "AZI Production Order" with attachments related to MO products
* Modify calculation of `date_planned_start` in MO
* Create a new model for `production.move.analysis`
* Add button in `product.template` to display MO
* Add button to display MO that has the same product in `stock.move`
* Add "Expand All" button in BOM Structure & Cost
* Create a new wizard to print compiled pdfs for `product.template` and `product.product`

Installation
============
* No specific installation required.

Configuration
=============
* No specific configuration required.

Usage
=====
* Bill of Materials: Manufacturing > Master Data > Bill of Materials > Choose a Bill of Materials > Components > Click on Attachments
* AZI Production Order: Manufacturing > Operations > Manufacturing Order > Choose MO > Print > AZI Production Order
* Production Picking: Manufacturing > Operations > Manufacturing Order > Choose MO > Print > Production Picking
* AZI Production Order with Attachments: Manufacturing > Operations > Manufacturing Order > Open MO > Action > Print: AZI Production Order with Attachments
* Production Move Analysis:  Manufacturing > Operations > Manufacturing Order >  Open MO > Move Analysis
* View MO in `product.template`: Inventory > Master Data > Products > Open a Product > Select Smart Button Called "Manufacturing"
* View MO in `stock.move`: Manufacturing > Operations > Manufacturing Order > Open MO > Consumed Materials > View MOs
* Expand All BOM: Manufacturing > Master Data > Bill of Materials > Open BOM > Structure & Cost > Click on "Expand All"
* Compiled PDFs for `product.template`: Inventory > Master Data > Products > Select a Product > Action > Compile PDFs
* Compiled PDFs for `product.product`: Inventory > Master Data > Product Variants > Select a Product > Action > Compile PDFs
