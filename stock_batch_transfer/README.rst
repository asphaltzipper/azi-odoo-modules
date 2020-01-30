====================
Stock Batch Transfer
====================
* Add a new field on `res.partner` which is `code`
* Set `sql_constraints` to make `code` field unique
* Override create and write to force code to be in uppercase
* Override copy to modify value of `code`


Installation
============
* No specific installation required.

Configuration
=============
* No specific configuration required.

Usage
=====
* Accounting > Customers > Customers > "Create / Update Customer" > "Set code for company"