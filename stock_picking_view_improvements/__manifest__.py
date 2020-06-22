# -*- coding: utf-8 -*-
{
    'name': "Stock Picking View Improvements",

    'summary': """
    """,

    'description': """
This module adds improvements to the stock.pîcking form view:\n
        
-> Change the name of the "action_assign" button ("Check availability" -> "Reserve")

This module has been developed by François WYAIME @ AbAKUS it-solutions.
    """,

    'author': "ABAKUS IT-SOLUTIONS",
    'website': "http://www.abakusitsolutions.eu",

    'category': 'Stock',
    'version': '11.0.1.0',

    'depends': [
        'stock',
    ],

    'data': [
        'views/stock_picking.xml',
    ],

    'installable': True
}
