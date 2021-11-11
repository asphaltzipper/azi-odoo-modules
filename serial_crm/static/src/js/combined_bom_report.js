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
        'click .o_combined_bom_unfoldable': '_onClickUnfold',
        'click .o_combined_bom_foldable': '_onClickFold',
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
        $(event.currentTarget).toggleClass('o_combined_bom_foldable o_combined_bom_unfoldable fa-caret-right fa-caret-down');

    },
    get_bom_change: function(event) {
        var self = this;
        var $parent = $(event.currentTarget).closest('tr');
        var activeID = $parent.data('id');
        var parent_id = $parent.data('parent_id');
        var child_component_id = $parent.data('child_component_id');
        var level = $parent.data('level') || 0;
        return this._rpc({
              model: 'report.serial_crm.report_combined_bom',
              method: 'get_bom_change',
              args: [
                  activeID,
                  child_component_id,
                  level+1,
              ]
          })
          .then(function (result) {
              self.render_html(event, $parent, result);
          });
    },
    get_repair_order: function(event){
        var self = this;
        var $parent = $(event.currentTarget).closest('tr');
        var activeID = $parent.data('id');
        var lot_id = $parent.data('child_component_id');
        var level = $parent.data('level') || 0;
        return this._rpc({
              model: 'report.serial_crm.report_combined_bom',
              method: 'get_repair_order',
              args: [
                  lot_id,
                  activeID,
                  level+1,
              ]
          })
          .then(function (result) {
              self.render_html(event, $parent, result);
          });
    },
    get_mo_component: function(event){
        var self = this;
        var $parent = $(event.currentTarget).closest('tr');
        var activeID = $parent.data('id');
        var level = $parent.data('level') || 0;
        return this._rpc({
              model: 'report.serial_crm.report_combined_bom',
              method: 'get_mo_component',
              args: [
                  activeID,
                  level+1,
              ]
          })
          .then(function (result) {
              self.render_html(event, $parent, result);
          });
    },
    _removeLines: function ($el) {
        var self = this;
        var activeID = $el.data('id');
        _.each(this.$('tr[parent_id='+ activeID +']'), function (parent) {
            var $parent = self.$(parent);
            var $el = self.$('tr[parent_id='+ $parent.data('id') +']');
            if ($el.length) {
                self._removeLines($parent);
            }
            $parent.remove();
        });
    },
    _onClickUnfold: function (ev) {
        var redirect_function = $(ev.currentTarget).data('function');
        this[redirect_function](ev);
    },
    _onClickFold: function (ev) {
        this._removeLines($(ev.currentTarget).closest('tr'));
        $(ev.currentTarget).toggleClass('o_combined_bom_foldable o_combined_bom_unfoldable fa-caret-right fa-caret-down');
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
