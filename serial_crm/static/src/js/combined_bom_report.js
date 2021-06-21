odoo.define('serial_crm.combined_bom_report', function (require) {
'use strict';

var core = require('web.core');
var framework = require('web.framework');
var stock_report_generic = require('stock.stock_report_generic');

var QWeb = core.qweb;
var _t = core._t;

var CombinedBomReport = stock_report_generic.extend({
    events: {
        'click .o_combined_bom_action': '_onClickAction',
    },
    get_html: function() {
        var self = this;
        var args = [this.given_context.active_id,];
        return this._rpc({
                model: 'report.serial_crm.report_combined_bom',
                method: 'get_html',
                args: args,
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
    render_html: function(event, $el, result){
        $el.after(result);
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

core.action_registry.add('combined_bom_report', CombinedBomReport);
return CombinedBomReport;

});
