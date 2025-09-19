# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountServiceProfitReport(models.Model):
    _name = "account.service.profit.report"
    _description = "Customer Service Profit"
    _auto = False
    _rec_name = 'invoice_date'

    move_id = fields.Many2one('account.move', 'Invoice')
    partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)
    salesperson_id = fields.Many2one('res.users', 'Salesperson', readonly=True)
    sales_team_id = fields.Many2one('crm.team', 'Sales Team', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    invoice_date = fields.Date('Invoice Date', readonly=True)
    quantity = fields.Float('Product Quantity', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    product_categ_id = fields.Many2one('product.category', 'Product Category', readonly=True)
    cost = fields.Float('Cost')
    list_price = fields.Float('List Price')
    discount_reason_id = fields.Many2one('sale.discount.reason', 'Discount Reason')
    move_line_id = fields.Many2one('account.move.line', 'Invoice Line')
    sales_amount = fields.Float()
    margin = fields.Float()
    margin_percent = fields.Float()

    _depends = {
        'account.move': [
            'move_type', 'partner_id', 'invoice_user_id', 'invoice_date',
        ],
        'account.move.line': [
            'quantity', 'price_total',  'balance',
            'move_id', 'product_id',
        ],
        'product.product': ['product_tmpl_id'],
        'product.template': ['categ_id'],
    }

    @property
    def _table_query(self):
        return self._select_customer_service()

    @api.model
    def _select_customer_service(self):
        return '''
            SELECT
                line.id,
                line.id AS move_line_id,
                line.move_id,
                line.product_id,                  
                line.company_id,
                sol.purchase_price * line.quantity AS cost,
                template.list_price,
                (line.price_subtotal - (sol.purchase_price * line.quantity)) AS margin,
                CASE WHEN line.price_subtotal != 0
                     THEN ((line.price_subtotal - (sol.purchase_price * line.quantity)) / line.price_subtotal) * 100
                     ELSE 0 END AS margin_percent,
            
                move.state,             
                move.move_type,              
                move.partner_id,              
                move.invoice_user_id AS salesperson_id,   
                line.discount_reason_id,          
                move.invoice_date,             
                template.categ_id AS product_categ_id,
                line.quantity AS quantity,                  
                line.price_total AS sales_amount,              
                line.currency_id  AS currency_id, 
                move.team_id AS sales_team_id          
            FROM account_move_line line               
                LEFT JOIN res_partner partner ON partner.id = line.partner_id              
                LEFT JOIN product_product product ON product.id = line.product_id               
                LEFT JOIN account_account account ON account.id = line.account_id             
                LEFT JOIN product_template template ON template.id = product.product_tmpl_id                       
                INNER JOIN account_move move ON move.id = line.move_id
                LEFT JOIN sale_order_line_invoice_rel sol_rel ON sol_rel.invoice_line_id = line.id
                LEFT JOIN sale_order_line sol ON sol.id = sol_rel.order_line_id
            WHERE move.move_type IN ('out_invoice', 'out_refund')        
                AND line.display_type = 'product'

        '''

