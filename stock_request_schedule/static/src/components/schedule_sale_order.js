/** @odoo-module */

import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
import { ControlPanel } from "@web/search/control_panel/control_panel";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";
const { Component, xml, onWillStart, useState, onWillUpdateProps } = owl;

export class ScheduleSOReport extends Component {
    setup() {
        super.setup();
        this.actionService = useService("action");
        this.rpc = useService("rpc");
        this.env.config.viewSwitcherEntries = [];
        this.orm = useService("orm");
        this.state = useState({
            controlPanelDisplay: true,
            unscheduleWithoutReserved: [],
            scheduleSOWithReserved: [],
            scheduleSOWithDiff: [],
            scheduleSOWithEarlyDate: [],
            scheduleSOWithLateDate: [],
            scheduleSONotConfirmed: [],


        });
        onWillStart(async () => {
            await this.get_html();
        });
    }


    async get_html() {
        const data  = await this.orm.call(
            'report.stock_request_schedule.report_schedule_so',
            'get_html',
            [],
            {},
        )
        console.log('data', data)
        this.state.unscheduleWithoutReserved = data['unschedule_without_reserved']
        this.state.scheduleSOWithReserved = data['schedule_so_with_reserved']
        this.state.scheduleSOWithDiff = data['schedule_so_with_diff_product']
        this.state.scheduleSOWithEarlyDate = data['schedule_so_with_early_date']
        this.state.scheduleSOWithLateDate = data['schedule_so_with_late_date']
        this.state.scheduleSONotConfirmed = data['schedule_so_not_confirmed']

    }
    async goToAction(e) {
        const resId = parseInt(e.target.dataset.resId)
        return this.actionService.doAction({
            type: 'ir.actions.act_window',
            res_model: e.target.dataset.model,
            res_id: resId,
            views: [[false, 'form']],
            target: 'current'
        });
    }


}
ScheduleSOReport.template = 'stock_request_schedule.ScheduleSOReport';

ScheduleSOReport.components = {
    ControlPanel,
};


registry.category("actions").add("schedule_so_report", ScheduleSOReport);
