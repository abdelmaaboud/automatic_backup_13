{
    'name': "Attachments for Company auto sent for specific emails",
    'version': '11.0.1.0',
    'depends': [
        'base',
        'mail',
    ],
    'author': "ABAKUS IT-SOLUTIONS",
    'website': "http://www.abakusitsolutions.eu",
    'category': 'Base',
    'data': [
        'views/base_company_view.xml',
        'views/res_partner_view.xml',

        'security/ir.model.access.csv',
    ],
}
