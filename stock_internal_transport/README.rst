========================
Stock Internal Transport
========================

* Create new fields in `res.company`, `stock.picking` and `stock.picking.type`
* Create new report for "Transport Document" in `stock.picking`
* Modify views of `res.company`, `stock.picking` and `stock.picking.type` to display newly created fields
* Create a new sequence for transport
* Create a new `stock.picking.type` that has a sequence related to transport

Installation
============
* No specific installation required.

Configuration
=============
* Inventory > Configuration > Settings > Traceability > (Enable Lots & Serial Numbers)
* Inventory > Configuration > Settings > Traceability > (Enable Display Lots & Serial Numbers)
* Inventory > Configuration > Settings > Warehouse > (Enable Storage Location)

Usage
=====
* `res.company` View: Settings > Users & Companies > Companies > Open Form View> General Information
* `stock.picking.type` View: Inventory > Configuration > Warehouse Management > Operations Types > Open Form View
* `stock.picking` View: Inventory > Operations > Transfers > Open Form View
* Transport Document Report: Inventory > Operations > Transfers > Select a transfer > Print > "Transport Document"
* Transport sequence: Settings > Technical > Sequences & Identifiers > Sequences > Search for (TRN)
* Transport Picking Type: Inventory > Configuration > Warehouse Management > Operations Types > Search for (Transport)