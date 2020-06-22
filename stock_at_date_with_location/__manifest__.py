{
    'name': 'Stock at date',
    'category': 'Stock',
    'summary': 'Show stock at date with locations',
    'author': 'ABAKUS IT-SOLUTIONS',
    'maintainer': 'ABAKUS IT-SOLUTIONS',
    'website': 'http://www.abakusitsolutions.eu/',
    'version': '11.0.1.0',
    'license': 'AGPL-3',
    'depends': [
        'stock',
    ],
    'data': [
        'views/stock_quant_date.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False
}