{
    'name': "Depreciation Schedule Report",
    'version': '11.0.1.0',
    'depends': [
        'account',
        'account_reports',
        'account_asset',
    ],
    'author': "ABAKUS IT-SOLUTIONS",
    'website': "http://www.abakusitsolutions.eu",
    'category': 'Accounting',
    'data': [
        'data/depreciation_schedule_data.xml',
        'views/report_financial.xml',
    ],
    'application': False,
    'installable': True,
}
