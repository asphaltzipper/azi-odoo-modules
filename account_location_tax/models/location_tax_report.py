# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools

class SalesTaxByLocation(models.Model):
    _name = 'sales.tax.by.location'
    _auto = False


    # # these fields selected from the database view
    partner_id = fields.Many2one(comodel_name='res.partner', string='Partner')
    state_id = fields.Many2one(comodel_name='res.country.state', string='State')
    city = fields.Char(string='City')
    zip = fields.Char(string='Zip')
    invoice_id = fields.Many2one(comodel_name='account.invoice', string='Invoice')
    invoice_number = fields.Char(related='invoice_id.number', string='Number')
    invoice_date = fields.Date(string='Date')
    account_id = fields.Many2one(comodel_name='account.account', string='Account')
    amount_untaxed = fields.Float(string='Untaxed')
    inv_tax_amt = fields.Float(string='Tax')
    amount_total = fields.Float(string="Total Amount")
    #
    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'sales_tax_by_location')
        self._cr.execute("""
            CREATE VIEW sales_tax_by_location AS (
            select
                i.id,
                i.id as invoice_id,
                i.date_invoice as invoice_date,
                l.account_id,
                i.partner_shipping_id as partner_id,
                coalesce(sp.state_id, p.state_id, pp.state_id) as state_id,
                coalesce(sp.city, p.city, pp.city) as city,
                coalesce(sp.zip,  p.zip, pp.zip) as zip,
                round(i.amount_untaxed::numeric, 4) as amount_untaxed,
                round(l.inv_tax_amt::numeric, 4) as inv_tax_amt,
                round(i.amount_total::numeric, 4) as amount_total
            from (
                select
                    account_id,
                    invoice_id,
                    sum(-1*balance) as inv_tax_amt
                from account_move_line
                where tax_line_id is not null
                group by account_id, invoice_id
            ) as l
            left join account_invoice as i on i.id=l.invoice_id
            left join res_partner as sp on sp.id=i.partner_shipping_id
            left join res_partner as p on p.id=i.partner_id
            left join res_partner as pp on pp.id=p.parent_id
            where i.type in ('out_invoice', 'out_refund')
            )
        """)


