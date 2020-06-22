# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
{
    'name': "Remittance Advice on Payment Orders",
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': "ABAKUS IT-SOLUTIONS",
    'website': "http://www.abakusitsolutions.eu",
    'depends': [
        'account_payment_order',
        'account_payment_partner',
        'account_payment_structured_communication',
    ],
    'category': 'Accounting',
    'data': [
        'views/res_partner_view.xml',
        'views/account_payment_line.xml',
        'views/account_payment.xml',
        'data/remittance_advice_mail_template.xml',
    ],
}
