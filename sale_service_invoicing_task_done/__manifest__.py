{
    'name': "Sale Service Invoicing Task Done",
    'version': '11.0.1.0',
    'depends': [
        'sale',
        'project',
        'sale_timesheet_delivered_quantity'
    ],
    'author': "Aktiv Software, ABAKUS IT-SOLUTIONS",
    'website': "http://www.abakusitsolutions.eu",
    'category': 'Sale',
    'description':
        """
    Sale Service Invoicing Task Done
    
    This module adjusts sale line delivered quantity to only if sale order line product has 'Invoice Base on Closed Task' as invoice policy 
    
        """,
    'data': [],
}
