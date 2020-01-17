Purchase Line Delivery
======================
* Add `po_carrier_id` in `res.config.settings` to be displayed in settings of purchase
* Add `carrier_id` in `purchase.order.line`
* Add `default_carrier_id` in `purchase.order` and create a new method which set `carrier_id` in `purchase.order.line` to have same value of `default_carrier_id`
* Modify report of 'Purchase Order' and 'Request for Quotation'


Installation
============
* No specific installation required.

Configuration
=============
* you can set `po_carrier_id` if you want: Purchase > Configuration > Settings > Logistics

Usage
=====
* For Modification in View or Report: Purchase > Purchase > Requests for Quotation
* Default Purchase Carrier: Purchase > Configuration > Settings > Logistics
