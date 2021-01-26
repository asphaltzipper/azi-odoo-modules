odoo.define('azi_barcodes.FormView', function (require) {
"use strict";

var core = require('web.core');
var FormController = require('web.FormController');

var _t = core._t;


FormController.include({
    _barcodeAddX2MQuantity: function (barcode, activeBarcode) {
        var record = this.model.get(this.handle);
        var candidate = this._getBarCodeRecord(record, barcode, activeBarcode);
        if (candidate) {
            return this._barcodeSelectedCandidate(candidate, record, barcode, activeBarcode);
        } else {
            return this._barcodeWithoutCandidate(record, barcode, activeBarcode);
        }
    },


});


});
