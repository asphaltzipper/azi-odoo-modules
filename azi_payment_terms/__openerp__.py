# -*- coding: utf-8 -*-
{
    'name' : 'AZI Payment Terms',
    'version' : '0.1',
    'author' : 'scosist',
    'description' : 'Import payment terms for AZI into account.payment.term' \
    ' and account.payment.term.line',
    'category' : 'Technical Settings',
    'depends' : ['base'],
    'data' : [
        'account_payment_term_data.xml',
        'account_payment_term_line_data.xml',
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
