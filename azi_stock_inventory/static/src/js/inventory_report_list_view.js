/** @odoo-module */

import { listView } from "@web/views/list/list_view";
import { InventoryReportListModel } from "@stock/views/list/inventory_report_list_model";
import { CustomInventoryReportListController } from "./inventory_report_list_controller";
import { registry } from "@web/core/registry";

export const InventoryReportListView = {
    ...listView,
    Model: InventoryReportListModel,
    Controller: CustomInventoryReportListController,
    buttonTemplate: 'InventoryReport.Buttons',
};

registry.category("views").add('inventory_report_list', InventoryReportListView);
