{
    'name': "ABAKUS invoice improvements",
    'version': '11.0.1.0',
    'depends': ['account', 'sale', 'sale_management'],
    'author': "ABAKUS IT-SOLUTIONS",
    'website': "http://www.abakusitsolutions.eu",
    'category': 'Accounting',
    'data': [
        'views/account_invoice_view.xml',
        'views/account_move_line_view.xml',
        'views/sale_order.xml',
        'wizards/sale_make_invoice_advance.xml',
    ],
}
