{
    'name': "Deliveries labels printing",
    'version': '11.0.1.0',
    'depends': [
        'sale',
        'stock'
    ],
    'author': "ABAKUS IT-SOLUTIONS",
    'website': "http://www.abakusitsolutions.eu",
    'category': 'Stock',
    'data': [
        'views/sale_order.xml',
        'views/stock_picking.xml',

        'reports/deliveries_labels.xml',
        'reports/picking_product_labels.xml',
        
        'data/report_paperformat_data.xml',
    ],
}
