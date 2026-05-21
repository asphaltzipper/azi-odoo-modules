# Technical Service Bulletin

For tracking upgrades to serialized units.

## Completing Upgrades

It's best to associate a TSB affected unit (TSB Serial) with either a helpdesk ticket,
sales order, or repair order.

The following guide, for deciding which business document is appropriate, is helpful but
not absolute.

- Helpdesk Ticket: when we provide no labor or materials to perform the upgrade
  - One ticket per customer
  - May reference multiple TSBs
  - May reference multiple serialized units
- Sales Order: when we provide materials for the customer to do their own upgrade
  - One order per customer
  - May reference multiple TSBs
  - May reference multiple serialized units
- Repair Order: when we perform the upgrade
  - One order per serialized unit
  - May reference multiple TSBs

Use the `Set TSB to Done` action, of the associated business document, to mark
serialized units as complete.

## To Do

Add links to helpdesk tickets.
