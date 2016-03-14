odoo.define('planner_barcode.planner', function (require) {
"use strict";

var planner = require('web.planner.common');

planner.PlannerDialog.include({
    prepare_planner_event: function() {
        this._super.apply(this, arguments);
        var self = this;

        // Once a barcode scan is completed, show if the scanner used a carriage return suffix
        if (self.planner.planner_application === 'planner_barcode') {
            self.$('.carriage-return').hide();
            var cr_timeout = null;
            self.$el.on('keypress', '.barcode-scanner', function(ev) {
                clearTimeout(cr_timeout);
                if (ev.which === 13) {
                    show_cr_result(true);
                } else {
                    cr_timeout = setTimeout(_.bind(show_cr_result, false), 100);
                }
            });
            var show_cr_result = function(cr_inputted) {
                self.$('.carriage-return').show();
                if (cr_inputted) {
                    self.$('.carriage-return span').addClass('label-success').removeClass('label-danger').text('ON');
                } else {
                    self.$('.carriage-return span').addClass('label-danger').removeClass('label-success').text('OFF');
                }
            };
        }
    }
});

});
