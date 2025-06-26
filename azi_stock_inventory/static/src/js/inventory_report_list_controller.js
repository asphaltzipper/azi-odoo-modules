/** @odoo-module */

import { useBus } from "@web/core/utils/hooks";
import { session } from "@web/session";
import { ListController } from "@web/views/list/list_controller";
import {InventoryReportListController} from "@stock/views/list/inventory_report_list_controller";

export class CustomInventoryReportListController extends InventoryReportListController {

    async onClickApplyAll() {
        let domain  = this.props.domain;
        if(this.props.context.active_model === 'stock.inventory'){
            domain = [['current_inventory_id', '=', this.props.context.active_id]]
        }
        const activeIds = await this.model.orm.search(this.props.resModel, domain, {
            limit: session.active_ids_limit,
            context: this.props.context,
        });
        return this.actionService.doAction("stock.action_stock_inventory_adjustement_name", {
            additionalContext: {
                active_ids: activeIds,
            },
            onClose: () => {
                this.model.load();
            },
        });
    }

}
