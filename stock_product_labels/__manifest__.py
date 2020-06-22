# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
{
    'name': "Product Stock Labels",
    'version': '11.0.1.0',
    'author': "ABAKUS IT-SOLUTIONS",
    'license': 'AGPL-3',
    'depends': [
        'stock',
        'sale',
        'product_brand'
    ],
    'website': 'http://www.abakusitsolutions.eu',
    'summary': 'Stocked product Labels',
    'category': 'Warehouse',
    'data': [
        'report/product_stock_label.xml',
        'views/product_labels_view.xml',
    ],
}
