Product Weight LBs
==================
* Add `weight_in_lbs` in `product.template` and `product.product`
* Modify calculation of weight in `product.product`
* Add `weight_in_lbs` and `shipping_weight_in_lbs` in `stock.picking` and `stock.quant.package`
* Add `shipping_weight` in `stock.quant.package`

Installation
============
* No specific installation required.

Configuration
=============
* Inventory > Configuration > Settings > Operations > Enable (Delivery Packages)

Usage
=====
* For new field in `product.template`: Inventory > Master Data > Products > Select a product > Inventory Tab > Logistics
* For new field in `product.product`: Inventory > Master Data > Product Variants >  Select a product > Inventory Tab > Logistics
* For new fields in `stock.picking`: Inventory > Operations > Transfers > Select a transfer > Additional Info. Tab
* For new fields in `stock.quant.package`: Inventory > Master Data > Packages > Select a package

