{
    'name': "Subscriptions in Leads",
    'version': '11.0.1.0',
    'depends': [
        'sale_crm',
        'sale_subscription',
    ],
    'author': "ABAKUS IT-SOLUTIONS",
    'website': "http://www.abakusitsolutions.eu",
    'category': 'CRM',
    'data': [
        'views/crm_lead_views.xml',
        'views/sale_subscription_view_form.xml',
    ],
    'application': False,
    'installable': True,
}
