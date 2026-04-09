/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";

patch(FormController.prototype, "azi_account_attachment_preview", {
    hasAttachmentViewer() {
        const hasViewer = this._super(...arguments);
        if (hasViewer) {
            if (this.model.root.resModel === 'account.move' && this.model.root.data) {
                const moveType = this.model.root.data.move_type;
                if (moveType && moveType !== 'in_invoice') {
                    return false;
                }
            }
        }
        return hasViewer;
    }
});