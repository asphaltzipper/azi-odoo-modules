AZI Account
====================
* Add a new field in `account.move.line`
* Modify report of invoice and create new report with no header and footer for invoice
* Override `_get_move_vals` in `account.payment` to modify value of `ref`
* Add `product_id` in reconciliation lines
* Modify tree view in `account.move.line`, form view in `account.move`, form view in `account.invoice` and add a new filters in `account.invoice`


Installation
============
* No specific installation required.

Configuration
=============
* No specific configuration required.

Usage
=====
* Invoices no header/footer report: Accounting > Customers > Invoices > Select an invoice and print report
* For product_id in reconciliation :Accounting > Overview > From dashboard Reconcile Items > play button to reconcile
* new filters in invoice: Accounting > Customers > Invoices
* `account.move` form view: Accounting > Accounting > Journal Entries > open a journal entry
* `account.move.line` tree view: Accounting > Accounting > Journal Items
* `account.invoice` form view: Accounting > Customers > Invoices > open an invoice