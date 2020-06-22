# -*- coding: utf-8 -*-
{
    'name': 'Dashboard KPI',
    'version': '11.0.1.0',
    'summary': 'KPI Management',
    'description': """
KPI Management in Odoo.
===========================
Support following features:
    * KPI management
    * KPI last date and compute value
    * KPI access to list of users
    * KPI computation method
    * KPI recorded values management

To use it, we need other modules for specific KPI computation that will inherit from the base model.
    """,
    'author': 'AbAKUS it-solutions',
    'website': 'http://abakusitsolutions.eu',
    'category': 'Reporting',
    'sequence': 0,
    'depends': [
        'board',
        'mail',
    ],
    'demo': [],
    'data': [
        'security/ir.model.access.csv',
        'security/kpi_record_rules.xml',

        'views/board_kpi_view.xml',
        'views/board_kpi_value_view.xml',
        'views/board_kpi_category_view.xml',

        'data/kpi_data.xml',
        
        'report/mail_templates.xml',
    ],
    'installable': True,
    'application': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
