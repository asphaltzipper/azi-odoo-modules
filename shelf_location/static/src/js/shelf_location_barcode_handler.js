odoo.define('shelf_location.ShelfLocationBarcodeHandler', function (require) {
    "use strict";
    var core = require('web.core');
    var Model = require('web.Model');
    var FormViewBarcodeHandler = require('barcodes.FormView');
    var _t = core._t;
    var ShelfLocationBarcodeHandler = FormViewBarcodeHandler.extend({
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
            this.sl_model = new Model("stock.shelf");
            this.form_view.options.disable_autofocus = 'true';
            if (this.form_view_initial_mode) {
                this.form_view.options.initial_mode = this.form_view_initial_mode;
            }
        },
        on_barcode_scanned: function(barcode) {
            var self = this;
            var sl_id = self.view.datarecord.id
            self.sl_model.call('sl_barcode',[barcode, sl_id]).then(function () {
                self.getParent().reload();
            });

        },
    });
    core.form_widget_registry.add('shelf_location_barcode_handler', ShelfLocationBarcodeHandler);
    return ShelfLocationBarcodeHandler;
});
