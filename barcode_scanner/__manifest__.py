# -*- coding: utf-8 -*-
{
    'name': "ABAKUS Barcode Scanner",

    'summary': """
        """,

    'description': """
    """,

    'author': "ABAKUS IT-SOLUTIONS",
    'website': "https://abakusitsolutions.eu",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Inventory',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base', 
        'contacts', 
        'website', 
        'bus', 
        'web',
        'stock',
        ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/barcode_scanner_templates.xml',
        'views/res_users.xml',
        'views/menu_item.xml',
        'data/paper_format.xml',
        #'reports/product_move_template.xml',
        'reports/product_label_internal.xml',
        'reports/product_label_out.xml'

    ],
}