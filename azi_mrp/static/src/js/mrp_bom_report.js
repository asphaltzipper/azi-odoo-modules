odoo.define('azi_mrp.mrp_bom_report', function (require) {
'use strict';

var core = require('web.core');
var MrpBomReport = require('mrp.mrp_bom_report');

var QWeb = core.qweb;
var _t = core._t;

var BOMReport = MrpBomReport.include({
    events: _.defaults({
        'click .expand_all_action': '_onClickExpandAll',
    }, MrpBomReport.prototype.events),

    expand_item: async function(item_to_expand){
        var self = this;
        var redirect_function = $(item_to_expand).data('function');
        if (redirect_function === 'get_bom'){
            await self.get_item_bom(item_to_expand);
        }
        if(redirect_function === 'get_operations'){
            await self.get_item_operations(item_to_expand);
        }

    },
    render_item_html: function(item_to_expand, $el, result){
        if (result.indexOf('mrp.document') > 0) {
            if (this.$('.o_mrp_has_attachments').length === 0) {
                var column = $('<th/>', {
                    class: 'o_mrp_has_attachments',
                    title: 'Files attached to the product Attachments',
                    text: 'Attachments',
                });
                this.$('table thead th:last-child').after(column);
            }
        }
        $el.after(result);
        $(item_to_expand).toggleClass('o_mrp_bom_foldable o_mrp_bom_unfoldable fa-caret-right fa-caret-down');
        this._reload_report_type();
    },
    get_item_bom: async function(item_to_expand) {
      var self = this;
      var $parent = $(item_to_expand).closest('tr');
      var activeID = $parent.data('id');
      var productID = $parent.data('product_id');
      var lineID = $parent.data('line');
      var qty = $parent.data('qty');
      var level = $parent.data('level') || 0;
      var result = await this._rpc({
              model: 'report.mrp.report_bom_structure',
              method: 'get_bom',
              args: [
                  activeID,
                  productID,
                  parseFloat(qty),
                  lineID,
                  level + 1,
              ]
          })
      return self.render_item_html(item_to_expand, $parent, result);
    },
    get_item_operations: async function(item_to_expand) {
      var self = this;
      var $parent = $(item_to_expand).closest('tr');
      var activeID = $parent.data('bom-id');
      var qty = $parent.data('qty');
      var level = $parent.data('level') || 0;
      var result = await this._rpc({
              model: 'report.mrp.report_bom_structure',
              method: 'get_operations',
              args: [
                  activeID,
                  parseFloat(qty),
                  level + 1
              ]
          })
      return self.render_item_html(item_to_expand, $parent, result);
    },

    _onClickExpandAll: async function(e){
        var self = this;
        var all_bom_lines = document.getElementsByClassName('o_mrp_bom_unfoldable');
        while(all_bom_lines.length > 0){
            await self.expand_item(all_bom_lines[0])
        }
    },


});

});
