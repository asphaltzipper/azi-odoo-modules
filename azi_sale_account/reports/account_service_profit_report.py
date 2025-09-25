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
    discount_reason_id = fields.Many2one('sale.discount.reason', 'Discount Reason')
    move_line_id = fields.Many2one('account.move.line', 'Invoice Line')
    sales_amount = fields.Float()
    margin = fields.Float()
    sale_order_id = fields.Many2one('sale.order', 'Sale Order')

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
            select
                inc.move_line_id as id,
                am.id as move_id,
                coalesce(rp.parent_id, rp.id) as partner_id,
                am.invoice_user_id as salesperson_id,
                am.team_id as sales_team_id,
                am.company_id,
                am.invoice_date,
                inc.quantity,
                inc.product_id,
                pt.categ_id as product_categ_id,
                -- multiply income quantity by unit cost because there may be multiple
                -- income lines for the same product, and we don't know which cost line
                -- to match
                inc.quantity * coalesce(cst.balance, 0.0) / (case when cst.quantity is null or cst.quantity = 0 then 1.0 else cst.quantity end) as cost,
                inc.discount_reason_id,
                inc.move_line_id,
                inc.balance as sales_amount,
                inc.balance + inc.quantity * coalesce(cst.balance, 0.0) / (case when cst.quantity is null or cst.quantity = 0 then 1.0 else cst.quantity end) as margin,
                sol.order_id as sale_order_id
            from (
                -- income
                select
                    aml.id as move_line_id,
                    aml.move_id,
                    aml.product_id,
                    aml.discount_reason_id,
                    aml.quantity,
                    -1 * aml.balance as balance
                from account_move_line aml
                left join account_move am on am.id=aml.move_id
                left join account_account aa on aa.id=aml.account_id
                where am.move_type in ('out_invoice', 'out_refund')
                and aml.product_id is not null
                and aa.account_type='income'
                and am.state='posted'
                group by aml.id, aml.move_id, aml.product_id, aml.discount_reason_id, aml.quantity
            ) as inc
            left join (
                -- costs
                select
                    aml.move_id,
                    aml.product_id,
                    case when aml.product_id is not null then null else aml.name end as line_name,
                    sum(aml.quantity) as quantity,
                    sum(-1 * aml.balance) as balance
                from account_move_line aml
                left join account_move am on am.id=aml.move_id
                left join account_account aa on aa.id=aml.account_id
                where am.move_type in ('out_invoice', 'out_refund')
                and aa.account_type='expense_cogs_material'
                and am.state='posted'
                group by aml.move_id, aml.product_id, case when aml.product_id is not null then null else aml.name end
            ) as cst on cst.move_id=inc.move_id and cst.product_id=inc.product_id
            left join account_move am on am.id=inc.move_id
            left join product_product pp on pp.id=inc.product_id
            left join product_template pt on pt.id=pp.product_tmpl_id
            left join res_partner rp on rp.id=am.partner_id
            -- sale order lines can have multiple invoices, but so far...
            -- invoice lines are never associated with multiple sale order lines
            left join sale_order_line_invoice_rel sol_rel on sol_rel.invoice_line_id=inc.move_line_id
            left join sale_order_line sol on sol.id=sol_rel.order_line_id
        '''
