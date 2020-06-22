# -*- coding: utf-8 -*-

{
    'name': "AbAKUS Contract report",
    'version': '11.0.1.0',
    'depends': [
        'project',
        'sale',
        'account_analytic_account_improvements',
    ],
    'author': "ABAKUS IT-SOLUTIONS",
    'website': "http://www.abakusitsolutions.eu",
    'category': 'Contract',
    'description': 
    """Contract Report for AbAKUS Baseline Projects

This modules adds the possibility to print service prestation reports for contract for AbAKUS it-solutions.

It also adds a setting wizard for the date selection of prestation range.

This module has been developed by Bernard Delhez, intern @ AbAKUS it-solutions, under the control of Valentin Thirion.
    """,
    'data': [
        'wizards/contract_report_view.xml',
        'reports/contract_report.xml',
        'views/account_analytic_account_view.xml',
        'data/contract_report_action_data.xml',
    ],
}
