//odoo.azi_account = function(instance){
//
//    instance.account.abstractReconciliationLine.include({
//
//    prepareCreatedMoveLinesForPersisting: function(lines) {
//        var dicts = this._super(lines);
//        for (var i = 0; i < dicts.length; i++)
//            dicts[i]['journal_id'] = lines[i].journal_id;
//        return dicts;
//    },
//
//    prepareCreatedMoveLinesForPersisting: function(lines) {
//        lines = _.filter(lines, function(line) { return !line.is_tax_line });
//        return _.collect(lines, function(line) {
//            var dict = {
//                account_id: line.account_id,
//                name: line.label
//            };
//            // Use amount_before_tax since the amount of the newly created line is adjusted to
//            // reflect tax included in price in account_move_line.create()
//            var amount = line.tax_id ? line.amount_before_tax: line.amount;
//            dict['credit'] = (amount > 0 ? amount : 0);
//            dict['debit'] = (amount < 0 ? -1 * amount : 0);
//            if (line.tax_id) dict['tax_ids'] = [[4, line.tax_id, null]];
//            if (line.analytic_account_id) dict['analytic_account_id'] = line.analytic_account_id;
//            if (line.analytic_tag_ids) dict['analytic_tag_ids'] = [[6, 0, line.analytic_tag_ids]];
//            return dict;
//        });
//    },
//
//    });
//}


// https://www.odoo.com/forum/help-1/question/inherit-js-file-odoo-9-119251
// https://stackoverflow.com/questions/43064290/overriding-javascript-function-in-odoo-9
// use ".include(" rather than ".extend("
odoo.define('azi_account.aziReconciliationTags', function(require){
    "use strict";
    var core = require('web.core');
    var _t = core._t;
    var FieldMany2ManyTags = core.form_widget_registry.get('many2many_tags');


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

        // add analytic tags field to the reconciliation form
        start: function() {
            this.create_form_fields['analytic_tag_ids'] = {
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
            return this._super();
        },

        // TODO: super the fetchPresets method, rather than replace it
        // replace this function because I don't know how to super it
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
                            analytic_tag_ids: datum.analytic_tag_ids
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
                            analytic_tag_ids: datum.second_analytic_tag_ids
                        });
                    }
                    self.presets[datum.id] = preset;
                });
            });
            return $.when(deferred_last_update, deferred_presets);
        },

    });

    // store the analytic tags to the new account move line
    var aziReconciliationLine = accountReconciliation.abstractReconciliationLine.include({
        prepareCreatedMoveLinesForPersisting: function(lines) {
            var dicts = this._super(lines);
            for (var i=0; i<dicts.length; i++)
                if (lines[i].analytic_tag_ids) dicts[i]['analytic_tag_ids'] = [[6, 0, lines[i].analytic_tag_ids]];
            return dicts;
        },
    });

})
