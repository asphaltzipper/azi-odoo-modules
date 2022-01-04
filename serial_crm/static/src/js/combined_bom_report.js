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
        'click .expand_all_action': '_onClickExpandAll',
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
        $(event).toggleClass('o_combined_bom_foldable o_combined_bom_unfoldable fa-caret-right fa-caret-down');

    },
    get_bom_change: async function(event) {
        var self = this;
        var event_target = event.currentTarget ? event.currentTarget: event
        var $parent = $(event_target).closest('tr');
        var activeID = $parent.data('id');
        var parent_id = $parent.data('parent_id');
        var child_component_id = $parent.data('child_component_id');
        var level = $parent.data('level') || 0;
        var result = await this._rpc({
              model: 'report.serial_crm.report_combined_bom',
              method: 'get_bom_change',
              args: [
                  activeID,
                  child_component_id,
                  level+1,
              ]});
        return self.render_html(event_target, $parent, result);

    },
    get_repair_order: async function(event){
        var self = this;
        var event_target = event.currentTarget ? event.currentTarget: event
        var $parent = $(event_target).closest('tr');
        var activeID = $parent.data('id');
        var lot_id = $parent.data('child_component_id');
        var level = $parent.data('level') || 0;
        var result = await this._rpc({
              model: 'report.serial_crm.report_combined_bom',
              method: 'get_repair_order',
              args: [
                  lot_id,
                  activeID,
                  level+1,
              ]
          })
        return self.render_html(event_target, $parent, result);
    },
    get_mo_component: async function(event){
        var self = this;
        var event_target = event.currentTarget ? event.currentTarget: event
        var $parent = $(event_target).closest('tr');
        var activeID = $parent.data('id');
        var level = $parent.data('level') || 0;
        var result = await this._rpc({
              model: 'report.serial_crm.report_combined_bom',
              method: 'get_mo_component',
              args: [
                  activeID,
                  level+1,
              ]
          })
        return self.render_html(event_target, $parent, result);
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
    expand_item: async function(item_to_expand){
        var self = this;
        var redirect_function = $(item_to_expand).data('function');
        if (redirect_function === 'get_bom_change'){
            await self.get_bom_change(item_to_expand);
        }
        if(redirect_function === 'get_repair_order'){
            await self.get_repair_order(item_to_expand);
        }
        if(redirect_function === 'get_mo_component'){
            await self.get_mo_component(item_to_expand);
        }

    },
    _onClickExpandAll:async function(e){
        var self = this;
        var all_combined_lines = document.getElementsByClassName('o_combined_bom_unfoldable');
        while(all_combined_lines.length > 0) {
            await self.expand_item(all_combined_lines[0])
        }
    },

});
core.action_registry.add('combined_bom_report', CombinedBomReport);
return CombinedBomReport;

});
