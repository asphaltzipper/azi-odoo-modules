/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useBus, useService } from "@web/core/utils/hooks";
import rpc from "web.rpc";

const { Component, xml, useState } = owl;

export class MOBarcodeHandler extends Component {
    setup() {
        const barcode = useService("barcode");
        this.actionService = useService("action");
        useBus(barcode.bus, "barcode_scanned", (event) => this._onBarcodeScanned(event.detail.barcode));
    }
    _onBarcodeScanned(barcode) {
        this.props.update(barcode);
        this._barcodeHandleMoAction(barcode);

    }

    async _barcodeHandleMoAction(barcode) {
        const activeRecord = this.props.record;

        try {
            const action = await rpc.query({
                model: activeRecord.resModel,
                method: 'barcode_scanned_action',
                args: [[activeRecord.id], barcode],
            });
            if (action) {
                this.actionService.doAction(action)
            }
        } catch (error) {
            console.error('Error handling barcode action:', error);
        }
    }
}

MOBarcodeHandler.template = xml``;
MOBarcodeHandler.props = { ...standardFieldProps };

registry.category("fields").add("mo_barcode_handler", MOBarcodeHandler);
