// https://www.odoo.com/forum/help-1/question/inherit-js-file-odoo-9-119251
// https://stackoverflow.com/questions/43064290/overriding-javascript-function-in-odoo-9
// use ".include(" rather than ".extend("
odoo.define('azi_account.aziReconciliationTags', function(require){
    "use strict";
    var core = require('web.core');
    var _t = core._t;
    var FieldMany2ManyTags = core.form_widget_registry.get('many2many_tags');
    var FieldMany2One = core.form_widget_registry.get('many2one');
    var FieldBoolean = core.form_widget_registry.get('boolean');


    // TODO: report this bug
    // fix a suspected bug in the web module
    var webFormRelational = require('web.form_relational');
    var aziFieldMany2ManyTags = webFormRelational.FieldMany2ManyTags.include({
        add_id: function(id) {
//            if (this.get('value') == false) {
//                this.set({'value': [id]});
//            } else {
//                this.set({'value': _.uniq(this.get('value').concat([id]))});
//            }
            if (this.get('value') == false) {
                this.set({'value': []});
            }
            return this._super(id);
        },
    });


    var accountReconciliation = require('account.reconciliation');
    var aziReconciliation = accountReconciliation.abstractReconciliation.include({

        start: function() {
            this.create_form_fields['account_id']['index'] = 0
            this.create_form_fields['product_id'] = {
                // add product field to the reconciliation form
                id: "product_id",
                index: 5,
                corresponding_property: "product_id",
                label: _t("Product"),
                required: false,
                constructor: FieldMany2One,
                field_properties: {
                    relation: "product.product",
                    string: _t("Product"),
                    type: "many2one",
                },
            };
            this.create_form_fields['label']['index'] = 10
            this.create_form_fields['analytic_account_id']['index'] = 15
            this.create_form_fields['amount']['index'] = 20
            this.create_form_fields['analytic_tag_ids'] = {
                // add analytic tags field to the reconciliation form
                id: "analytic_tag_ids",
                index: 25,
                corresponding_property: "analytic_tag_ids",
                label: _t("Analytic Tags"),
                required: false,
                group:"analytic.group_analytic_accounting",
                constructor: FieldMany2ManyTags,
                field_properties: {
                    relation: "account.analytic.tag",
                    string: _t("Analytic Tags"),
                    type: "many2many_tags",
                },
            };
            this.create_form_fields['tax_id']['index'] = 30
            this.create_form_fields['has_receipt'] = {
                // add has_receipt field to the reconciliation form
                id: "has_receipt",
                index: 35,
                corresponding_property: "has_receipt",
                label: _t("Receipt on File"),
                required: false,
                constructor: FieldBoolean,
                field_properties: {
                    string: _t("Receipt on File"),
                    type: "boolean",
                },
            };
            return this._super();
        },

        // TODO: super the fetchPresets method, rather than replace it
        // replace this function because I don't know how to super it
        // fetching presets for analytic_tag_ids and product_id
        fetchPresets: function() {
            var self = this;
            var deferred_last_update = self.model_presets.query(['write_date']).order_by('-write_date').first().then(function (data) {
                self.presets_last_write_date = (data ? data.write_date : undefined);
            });
            var deferred_presets = self.model_presets.query().order_by('-sequence', '-id').all().then(function (data) {
                self.presets = {};
                _(data).each(function(datum){
                    var preset = {
                        id: datum.id,
                        name: datum.name,
                        sequence: datum.sequence,
                        lines: [{
                            account_id: datum.account_id,
                            journal_id: datum.journal_id,
                            label: datum.label,
                            amount_type: datum.amount_type,
                            amount: datum.amount,
                            tax_id: datum.tax_id,
                            analytic_account_id: datum.analytic_account_id,
                            analytic_tag_ids: datum.analytic_tag_ids,
                            product_id: datum.product_id,
                            has_receipt: datum.has_receipt
                        }]
                    };
                    if (datum.has_second_line) {
                        preset.lines.push({
                            account_id: datum.second_account_id,
                            journal_id: datum.second_journal_id,
                            label: datum.second_label,
                            amount_type: datum.second_amount_type,
                            amount: datum.second_amount,
                            tax_id: datum.second_tax_id,
                            analytic_account_id: datum.second_analytic_account_id,
                            analytic_tag_ids: datum.second_analytic_tag_ids,
                            product_id: datum.second_product_id,
                            has_receipt: datum.second_has_receipt
                        });
                    }
                    self.presets[datum.id] = preset;
                });
            });
            return $.when(deferred_last_update, deferred_presets);
        },

    });

    // store the analytic tags and product id to the new account move line
    var aziReconciliationLine = accountReconciliation.abstractReconciliationLine.include({
        prepareCreatedMoveLinesForPersisting: function(lines) {
            var dicts = this._super(lines);
            for (var i=0; i<dicts.length; i++) {
                if (lines[i].analytic_tag_ids) dicts[i]['analytic_tag_ids'] = [[6, 0, lines[i].analytic_tag_ids]];
                if (lines[i].product_id) dicts[i]['product_id'] = lines[i].product_id;
                if (lines[i].has_receipt) dicts[i]['has_receipt'] = true;
            }
            return dicts;
        },
    });

})
