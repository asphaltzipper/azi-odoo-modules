odoo.define('azi_account.aziReconciliationTags', function(require){
    "use strict";
    var core = require('web.core');
    var relational_fields = require('web.relational_fields');
    var basic_fields = require('web.basic_fields');
    var reconciliationRender = require('account.ReconciliationRenderer');
    var accountReconciliation = require('account.ReconciliationModel');
    var qweb = core.qweb;
    var _t = core._t;

    var aziReconciliation = accountReconciliation.ManualModel.include({
        quickCreateFields: ['account_id', 'journal_id', 'amount', 'analytic_account_id', 'name', 'tax_ids', 'force_tax_included', 'date', 'to_check', 'product_id'],

        _formatQuickCreate: function (line, values) {
            values = values || {};
            var prop = {}
            prop = this._super(line, values)
            prop.product_id =this._formatNameGet(values.product_id)
            return prop;
        },
        _formatToProcessReconciliation: function (line, prop) {
            var result = {}
            result = this._super(line, prop)
            if (prop.product_id) result.product_id = prop.product_id.id;
            return result;
        },
    });

    var aziReconciliationRender = reconciliationRender.ManualLineRenderer.include({
        _renderCreate: function (state) {
            var self = this;
            return this.model.makeRecord('account.bank.statement.line', [{
                relation: 'account.account',
                type: 'many2one',
                name: 'account_id',
                domain: [['company_id', '=', state.st_line.company_id], ['deprecated', '=', false]],
            }, {
                relation: 'account.journal',
                type: 'many2one',
                name: 'journal_id',
                domain: [['company_id', '=', state.st_line.company_id], ['type', '=', 'general']],
            }, {
                relation: 'account.tax',
                type: 'many2many',
                name: 'tax_ids',
                domain: [['company_id', '=', state.st_line.company_id]],
            }, {
                relation: 'account.analytic.account',
                type: 'many2one',
                name: 'analytic_account_id',
                domain: ["|", ['company_id', '=', state.st_line.company_id], ['company_id', '=', false]],
            },
            //Add product_id to be render
            {
                relation:'product.product',
                type:'many2one',
                name:'product_id'
            }, {
                type: 'boolean',
                name: 'force_tax_included',
            }, {
                type: 'char',
                name: 'name',
            }, {
                type: 'float',
                name: 'amount',
            }, {
                type: 'char', //TODO is it a bug or a feature when type date exists ?
                name: 'date',
            }, {
                type: 'boolean',
                name: 'to_check',
            }], {
                account_id: {
                    string: _t("Account"),
                },
                name: {string: _t("Label")},
                amount: {string: _t("Account")},
            }).then(function (recordID) {
                self.handleCreateRecord = recordID;
                var record = self.model.get(self.handleCreateRecord);

                self.fields.account_id = new relational_fields.FieldMany2One(self,
                    'account_id', record, {mode: 'edit', attrs: {can_create:false}});

                self.fields.journal_id = new relational_fields.FieldMany2One(self,
                    'journal_id', record, {mode: 'edit'});

                self.fields.tax_ids = new relational_fields.FieldMany2ManyTags(self,
                    'tax_ids', record, {mode: 'edit', additionalContext: {append_type_to_tax_name: true}});

                self.fields.analytic_account_id = new relational_fields.FieldMany2One(self,
                    'analytic_account_id', record, {mode: 'edit', attrs: {options:{quick_create: false, no_create_edit: true}}});

                //product
                self.fields.product_id = new relational_fields.FieldMany2One(self, 'product_id', record, {mode:'edit'})

                self.fields.force_tax_included = new basic_fields.FieldBoolean(self,
                    'force_tax_included', record, {mode: 'edit'});

                self.fields.name = new basic_fields.FieldChar(self,
                    'name', record, {mode: 'edit'});

                self.fields.amount = new basic_fields.FieldFloat(self,
                    'amount', record, {mode: 'edit'});

                self.fields.date = new basic_fields.FieldDate(self,
                    'date', record, {mode: 'edit'});

                self.fields.to_check = new basic_fields.FieldBoolean(self,
                    'to_check', record, {mode: 'edit'});

                var $create = $(qweb.render("reconciliation.line.create", {'state': state, 'group_acc': self.group_acc}));
                self.fields.account_id.appendTo($create.find('.create_account_id .o_td_field'))
                    .then(addRequiredStyle.bind(self, self.fields.account_id));
                self.fields.journal_id.appendTo($create.find('.create_journal_id .o_td_field'));
                self.fields.tax_ids.appendTo($create.find('.create_tax_id .o_td_field'));
                self.fields.analytic_account_id.appendTo($create.find('.create_analytic_account_id .o_td_field'));
                //product
                self.fields.product_id.appendTo($create.find('.create_product_id .o_td_field'));
                //
                self.fields.force_tax_included.appendTo($create.find('.create_force_tax_included .o_td_field'));
                self.fields.name.appendTo($create.find('.create_label .o_td_field'))
                    .then(addRequiredStyle.bind(self, self.fields.name));
                self.fields.amount.appendTo($create.find('.create_amount .o_td_field'))
                    .then(addRequiredStyle.bind(self, self.fields.amount));
                self.fields.date.appendTo($create.find('.create_date .o_td_field'));
                self.fields.to_check.appendTo($create.find('.create_to_check .o_td_field'));
                self.$('.create').append($create);

                function addRequiredStyle(widget) {
                    widget.$el.addClass('o_required_modifier');
                }

                self.$('.create .create_journal_id').show();
                self.$('.create .create_date').removeClass('d-none');
                self.$('.create .create_journal_id .o_input').addClass('o_required_modifier');
            });
        },
    });
});
