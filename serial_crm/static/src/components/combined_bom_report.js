/** @odoo-module */

import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
import { ControlPanel } from "@web/search/control_panel/control_panel";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";
const { Component, xml, onWillStart, useState, onWillUpdateProps } = owl;

export class CombinedBomReport extends Component {
    setup() {
        super.setup();
        this.actionService = useService("action");
        this.rpc = useService("rpc");
        this.env.config.viewSwitcherEntries = [];
        this.orm = useService("orm");
        this.state = useState({
            controlPanelDisplay: true,
            bomChanges: [],
            repairOrders: [],
            mos: [],
            productNames: {},
            expandedRepairLines: {},
            moCompLine: {},
            currentBom: {},
            bomLines: [],
            webParam: '',

        });
        onWillStart(async () => {
            await this.get_html();
            const webParam = await this.orm.call("ir.config_parameter", "get_param", ["web.base.url"])
            this.state.webParam = webParam;
        });
    }
    get activeId() {
        return this.props.action.context.active_id;
    }

    async goToAction(e) {
        const resId = parseInt(e.target.dataset.resId)
        return this.actionService.doAction({
            type: "ir.actions.act_window",
            res_model: e.target.dataset.model,
            res_id: resId,
            views: [[false, "form"]],
            target: "current",
            context: {
                active_id: resId,
            },
        });
    }
    get_html= async()=> {
        var args = [this.activeId,];
        const data  = await this.orm.call(
            'report.serial_crm.report_combined_bom',
            'get_html',
            args,
            {},
        )
        this.state.bomChanges = data["bom_changes"]
        this.state.repairOrders = data['repair_orders']
        this.state.mos = data['mo']

    }

}
CombinedBomReport.template = 'serial_crm.CombinedBomReport';

CombinedBomReport.components = {
    ControlPanel,
};


registry.category("actions").add("combined_bom_report", CombinedBomReport);
