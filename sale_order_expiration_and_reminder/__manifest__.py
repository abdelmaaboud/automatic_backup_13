# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
{
    'name': 'Sale Order Expiration and Reminders',
    'version': '11.0.1.0',
    'author': 'ABAKUS IT-SOLUTIONS',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'sale'
    ],
    'website': 'http://www.abakusitsolutions.eu',
    'category': 'Sale',
    'data': [
        'views/sale_order_view.xml',
        'views/res_config.xml',

        'data/ir_cron.xml',
        'data/email_template.xml',
    ],
}
