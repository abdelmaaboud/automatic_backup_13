{
    'name': "Supplier API Products Updater",
    'summary': "Updater for products using suppliers APIs.",
    'version': '11.0.1.0',
    'depends': [
        'purchase',
        'product_state',
    ],
    'author': "ABAKUS IT-SOLUTIONS",
    'website': "http://www.abakusitsolutions.eu",
    'category': 'Utilities',
    'data': [
        'views/supplier_updater_setting_view.xml',
        'views/product_supplierinfo_view.xml',
        'views/product_view.xml',

        'data/suppliers_product_updater_cron.xml',
        'data/model_rules.xml',

        'security/ir.model.access.csv',
    ],
}
