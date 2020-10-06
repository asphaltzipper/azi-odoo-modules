odoo.define('mrp_wo_produce.MOBarcodeHandler', function (require) {
    "use strict";

    var AbstractField = require('web.AbstractField');
    var field_registry = require('web.field_registry');
    var FormController = require('web.FormController');

    FormController.include({
        _barcodeHandleMoAction: function (barcode, activeBarcode) {
            console.log("Barcode handling")
            var record = this.model.get(this.handle);
            var self = this;
            var record = this.model.get(activeBarcode.handle);
            return self._rpc({
                    model: record.model,
                    method: 'barcode_scanned_action',
                    args: [[record.data.id], barcode],
                }).done(function (action) {
                    console.log("action", action)
                    if (action) {
                        self._barcodeStopListening();
                        self.do_action(action);
                    }
                });
        },
    });

    var MOBarcodeHandler = AbstractField.extend({
        init: function () {
            this._super.apply(this, arguments);
            this.trigger_up('activeBarcode', {
                name: this.name,
                commands: {
                    barcode: '_barcodeHandleMoAction',
                },
            });
        },
    });
    field_registry.add('mo_barcode_handler', MOBarcodeHandler);

    return MOBarcodeHandler;

});