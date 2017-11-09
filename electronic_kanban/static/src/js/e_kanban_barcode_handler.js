odoo.define('electronic_kanban.EKanbanBarcodeHandler', function (require) {
    "use strict";
    var core = require('web.core');
    var Model = require('web.Model');
    var FormViewBarcodeHandler = require('barcodes.FormViewBarcodeHandler');
    var _t = core._t;
    var EKanbanBarcodeHandler = FormViewBarcodeHandler.extend({
        init: function (parent, context) {
            if (parent.ViewManager.action) {
                this.form_view_initial_mode = parent.ViewManager.action.context.form_view_initial_mode;
            } else if (parent.ViewManager.view_form) {
                this.form_view_initial_mode = parent.ViewManager.view_form.options.initial_mode;
            }
            return this._super.apply(this, arguments);
        },
        start: function () {
            this._super();
            this.ekb_model = new Model("stock.e_kanban_batch");
            this.form_view.options.disable_autofocus = 'true';
            if (this.form_view_initial_mode) {
                this.form_view.options.initial_mode = this.form_view_initial_mode;
            }
        },
        on_barcode_scanned: function(barcode) {
            var self = this;
            var ekb_id = self.view.datarecord.id
            self.ekb_model.call('ekb_barcode',[barcode, ekb_id]).then(function () {
                self.getParent().reload();
            });

        },
    });
    core.form_widget_registry.add('e_kanban_barcode_handler', EKanbanBarcodeHandler);
    return EKanbanBarcodeHandler;
});
