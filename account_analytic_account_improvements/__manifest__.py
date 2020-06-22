# -*- coding: utf-8 -*-

{
    'name': "ABAKUS Sale Contract Management",
    'version': '11.0.1.0',
    'depends': [
        'sale_subscription',
        'project',
        'hr_timesheet',
        'account_invoicing',
        'account',
        'contract_timesheet_activities_on_site_management',
        'hr_analytic_timesheet_improvements',
    ],
    'author': "ABAKUS IT-SOLUTIONS",
    'website': "http://www.abakusitsolutions.eu",
    'category': 'Sales',
    'data': [
        'views/hr_timesheet_factor_view.xml',
        'views/account_analytic_line_view.xml',
        'views/account_analytic_account_team_view.xml',
        'views/account_analytic_account_view.xml',
        'views/sale_subscription_template_view.xml',
        'views/sale_subscription_view.xml',
        'views/project_project_view.xml',
        'views/hr_timesheet_view.xml',
        'views/account_move_line.xml',

        'data/to_invoice.xml',
        'data/ir_cron.xml',

        'security/ir.model.access.csv',
    ],
}
