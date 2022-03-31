odoo.define('stock_request_schedule.schedule_so_report', function (require) {
'use strict';

var core = require('web.core');
var framework = require('web.framework');
var stock_report_generic = require('stock.stock_report_generic');

var QWeb = core.qweb;
var _t = core._t;

var ScheduleSOReport = stock_report_generic.extend({
    events: {
        'click .o_schedule_so_action': '_onClickAction',
    },
    get_html: function() {
        var self = this;
        return this._rpc({
                model: 'report.stock_request_schedule.report_schedule_so',
                method: 'get_html',
                args: [],
                context: this.given_context,
            })
            .then(function (result) {
                self.data = result;
            });
    },
    set_html: function() {
        var self = this;
        return this._super().then(function () {
            self.$el.html(self.data.lines);
        });
    },
    _onClickAction: function (ev) {
        ev.preventDefault();
        return this.do_action({
            type: 'ir.actions.act_window',
            res_model: $(ev.currentTarget).data('model'),
            res_id: $(ev.currentTarget).data('res-id'),
            views: [[false, 'form']],
            target: 'current'
        });
    },


});
core.action_registry.add('schedule_so_report', ScheduleSOReport);
return ScheduleSOReport;

});
