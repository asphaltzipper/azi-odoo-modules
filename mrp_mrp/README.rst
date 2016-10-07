============================
Improved MRP-1 Functionality
============================

This module provides a material requirements planning system.  The system is composed of a table for planned orders, and an algorithm to create them.


Algorithm Details
=================

Simple MRP functionality to plan material orders which can be converted into Procurement Orders.  The planned orders are time phased, meaning that it schedules orders to deliver only the required quantity, and not until it it is needed.


Order Management Interface
==========================

In the list view, planned orders can be filtered by type and date.  The purchasing agent (buyer) will filter for purchased items, and the production planner will filter for manufactured items.  Users can convert planned orders into Procurement Orders, on a periodic basis (e.g. weekly).  This deletes the orders so that they won't be converted more than once.


Motivation for This Module
==========================


The Enterprise MPS Module
-------------------------

Odoo Enterprise includes module mrp_mps, which provides a master procurement schedule.  The Master Procurement Schedule offers features and functionality that are similar to material requirements planning.  However, it has a major limitation: It doesn't plan for dependent demand (components).  Planning for components of scheduled product requires that they are either included on the schedule, or planned by orderpoint rules.


The Run Schedulers Algorithm
----------------------------

The v10 scheduler algorithm (mostly implemented in _procure_orderpoint_confirm) has several problems:

* It should use a low-level-code for sequencing orderpoints. With the current algorithm, orderpoints are executed in the wrong order and some demand is not considered.
* It should time-phase MO/PO start dates by bucket (daily or weekly). The current algorithm schedules everything ASAP, rather than when they are needed.
* It should allow changes to independent demand (make-to-stock MOs).  The current algorithm only plans for components of confirmed MOs, which are difficult to change and delete.
* It should be able to delete previously scheduled supply when demand has changed from the last run of the algorithm.  The current algorithm will create thousands of Procurement Orders, MOs and POs.  Changing the plan requires the user to delete them when they are no longer needed.

These problems make it practically impossible to use the Scheduler for make-to-stock operations.  In short, the Run Schedulers algorithm is largely deficient in terms of providing MRP-1 functionality.

This module and its dependencies will implement real MRP.  This is MRP-1, not MRP-2, meaning that we do not consider manufacturing capacity.  We assume infinite manufacturing capacity.

Since this is MRP-1, it has all the usual problems of MRP:

* infinite capacity assumption
* zero delay for internal moves
* data integrity (garbage in, garbage out)
* nervousness
* bullwhip effect

But, it fixes the problems with the standard Odoo scheduler:

* low-level coding
* time phasing / buckets
* plan modification


Low-Level-Code
--------------

Odoo's current Scheduler considers reorder rules in the order they were created. When orderpoints are executed in the wrong order, some demand is not considered.  For example, consider the case where an orderpoint for a component is considered before that of its parent.  Say the current algorithm triggers an orderpoint for the parent, and generates an MO.  It should also trigger the orderpoint for the component and generate a PO.  But, the algorithm only considers each orderpoint once, and it has already considered the component's orderpoint and found no demand.  Therefore, the needed PO will not be created.

.. image:: http://www.asprova.jp/mrp/glossary/en/fig/mrp_188-2.jpg
   :alt: Low-Level-Code Diagram
   :target: http://www.asprova.jp/mrp/glossary/en/cat248/post-740.html

Low-Level-Coding is the industry standard. It is a fundamental concept in Material Requirements Planning.

Module mrp_llc implements the Low-Level-Code (LLC) in a simple and very efficient recursive query.  The query is stored in a database view, and associated with a new ORM model (mrp.bom.llc).  We then sort the orderpoints by LLC before executing them.


Time-Phase Buckets
------------------

The current scheduling algorithm schedules everything as soon as possible.  That is terribly inefficient in terms of inventory holding cost.  And, of course, it is also impossible to build all MOs at one time.

This MRP algorithm considers future demand and creates future supply, based on small time periods.  These small time periods are called buckets.  By default, the time buckets have size of one week.  Using time-phasing, we delay orders for components until the day they are needed.


Independent Demand
------------------

`Independent demand <https://en.wikipedia.org/wiki/Material_requirements_planning#Dependent_demand_vs_independent_demand>`_ may include the following:

* Confirmed Sales orders (customer demand)
* Manufacturing orders for finished product (make-to-stock demand)

We need to be able to change independent demand by canceling or deleting orders.  However, deleting confirmed MOs is messy.  We need a way to plan for make-to-stock type independent demand, and schedule supply for the raw materials.  And, we need to be able to change our plan.



Dependent Demand
----------------

In the current algorithm, stock moves are used to detect dependent demand for components of MOs.  This requires the MOs to be confirmed.  Once they are confirmed, they can't be changed or deleted.  That leaves the user with potentially hundreds of MOs that may need to be canceled when demand has changed.

With the MRP algorithm, MOs and POs are created when the user manually runs procurement orders.  This would be done in batches, at intervals, as needed (e.g. weekly).
