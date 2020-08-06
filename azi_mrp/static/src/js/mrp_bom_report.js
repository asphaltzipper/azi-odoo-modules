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

    _onClickExpandAll: function(e){
        var self = this;
        var all_bom_lines = document.getElementsByClassName('o_mrp_bom_unfoldable')
        for (var i =0; i< all_bom_lines.length; i++){
            all_bom_lines[i].click();
        }
        setTimeout(()=>{
            all_bom_lines = document.getElementsByClassName('o_mrp_bom_unfoldable');
            if (all_bom_lines.length > 0){
                var button = document.getElementsByClassName('expand_all_action');
                button[0].click();
            }
         }, 800)

    },


});

});
