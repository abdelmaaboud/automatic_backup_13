# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
{
    'name': "Account Filter on Payment Orders",
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': "ABAKUS IT-SOLUTIONS",
    'website': "http://www.abakusitsolutions.eu",
    'depends': [
        'account_payment_order',
        'account_payment_mode',
    ],
    'category': 'Accounting',
    'data': [
        'views/account_payment_mode.xml',
        'wizards/account_payment_line_create.xml',
    ],
}
