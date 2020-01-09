AZI Sale
====================
* Add new filters in `crm.team`
* Add new fields in `res.partner`, override `name_get` and `_compute_display_name` to display name of partner in different way
* Add new fields in `sale.order` and override `action_confirm` to do some validation first
* Add new field to calculate the remaining quantity to be delivered in `sale.order.line`
* Modify Quotation/Order Report and change attached name for it
* Modify form view of `res.partner` to add some attributes on fields and change kanaban view of contacts, also modify tree view
* Modify form view of `sale.order` and `account.invoice`
* Modify tree and search view for `sale.order.line` and display menuitem for `sale.order.line`

Installation
============
* No specific installation required.

Configuration
=============
* Sales > Configuration > Settings > Quotations & Orders > Enable (Sale Warnings)
* Sales > Configuration > Settings > Quotations & Orders > Enable (Customer Addresses)

Usage
=====
* `crm.team` filter: CRM > Configurations > Teams & Regions > Sales Teams
* `sale.order` Modification & Report: Sales > Orders > Quotations
* `res.partner` Modification: Sales > Orders > Customers
* `sale.order.line` Modification & Menu: Sales > Reporting > Sale Order Lines