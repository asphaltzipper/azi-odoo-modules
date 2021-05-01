AZI Stock
=========
* Adding constraint in `stock.quant` to prevent creating a new record in
  `stock.quant` when the picking type is internal and product is tracked by serial number
* Adding field in `stock.move.line`
* Adding a field and modifying the views of `stock.picking` and `stock.move`
* Modifying "Picking Operations" report to display "Completed Date"
* Create label reports for `product.product`, `product.template` and
  `stock.move`, also create paper format

Installation
============
For barcode fonts, follow the installation instructions for module barcode_font.

Configuration
=============
* You need to enable "Show Detailed Operations" in Inventory > Configuration > Operations types

Usage
=====
* To check constraint for `stock.quant` we need to create internal picking for
  product that is tracked by serial by going to Inventory > Operations >
  Transfer
* Picking operations report: Inventory > operations > Transfer > Print
* AZI Product Labels report: Inventory > Master Data > Products or Inventory >
  Master Data > Product Variants
* New view of stock quant: Inventory > Reporting > FG Stock Valuation
* Transfer Slip report: Inventory > Reporting > Stock Moves
* AZI Location Labels report: Inventory > Master Data > Stock Shelf
