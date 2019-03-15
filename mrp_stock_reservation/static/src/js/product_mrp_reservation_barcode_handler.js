odoo.define('mrp_stock_reservation.ProductMrpReservationBarcodeHandler', function (require) {
    "use strict";
    var core = require('web.core');
    var Model = require('web.Model');
    var FormViewBarcodeHandler = require('barcodes.FormViewBarcodeHandler');
    var _t = core._t;
    var ProductMrpReservationBarcodeHandler = FormViewBarcodeHandler.extend({
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
            this.mrp_res_model = new Model("product.product");
            this.form_view.options.disable_autofocus = 'true';
            if (this.form_view_initial_mode) {
                this.form_view.options.initial_mode = this.form_view_initial_mode;
            }
        },
        on_barcode_scanned: function(barcode) {
            var self = this;
            var current_id = self.view.datarecord.id
            self.mrp_res_model.call('mrp_res_barcode',[barcode, current_id]).then(function (new_action) {
                if (new_action) {
                    var options = {"clear_breadcrumbs": true}
                    self.do_action(new_action, options);
                } else {
                    self.getParent().reload();
                }
            });

        },
    });
    core.form_widget_registry.add('product_mrp_reservation_barcode_handler', ProductMrpReservationBarcodeHandler);
    return ProductMrpReservationBarcodeHandler;
});
