/** @odoo-module **/

import { registry } from '@web/core/registry';
import { Many2OneField } from '@web/views/fields/many2one/many2one_field';



export class PurchaseLineProductField extends Many2OneField {
    setup() {
        super.setup();
        const super_update = this.update;
        this.update = (recordlist) => {
            if (recordlist && recordlist.length > 0 && recordlist[0].name) {
                const displayName = recordlist[0].name;
                if (displayName.startsWith('[')) {
                    const code = displayName.split(']')[0].substring(1);
                    if (this.props.record.fields.vendor_product_code) {
                        this.props.record.update({ vendor_product_code: code });
                    }
                }
            }
            super_update(recordlist);
        };


    }


}

registry.category("fields").add("purchase_product_field", PurchaseLineProductField);