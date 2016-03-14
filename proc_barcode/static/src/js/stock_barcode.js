odoo.define('proc_barcode.MainMenu', function (require) {
"use strict";

var core = require('web.core');
var Model = require('web.Model');
var Widget = require('web.Widget');
var Session = require('web.session');
var BarcodeHandlerMixin = require('barcodes.BarcodeHandlerMixin');

var MainMenu = Widget.extend(BarcodeHandlerMixin, {
    template: 'main_menu',

    events: {
        "click .button_proc_operations": function(){
          //  this.on_barcode_scanned("123");
            this.do_action('proc_barcode.proc_action_form')
        },
    },

    on_attach_callback: function() {
        this.start_listening();
    },

    on_detach_callback: function() {
        this.stop_listening();
    },

    on_barcode_scanned: function(barcode) {
        var self = this;
        Session.rpc('/proc_barcode/scan_from_main_menu', {
            barcode: barcode,
        }).then(function(result) {
            if (result.action) {
                self.do_action(result.action);
            } else if (result.warning) {
                self.do_warn(result.warning);
            }
        });
    },
});

core.action_registry.add('proc_barcode_main_menu', MainMenu);

return {
    MainMenu: MainMenu,
};

});
