# -*- coding: utf-8 -*-

{
    'name': "ABAKUS OS/SD Timesheet Management",
    'version': '11.0.1.0',
    'depends': [
        'sale_subscription',
        'project',
        'hr_timesheet',
    ],
    'author': "ABAKUS IT-SOLUTIONS",
    'website': "http://www.abakusitsolutions.eu",
    'category': 'Sales',
    'data': [
        'views/sale_subscription_view.xml',
        'views/project_task_view.xml',
        'views/hr_analytic_timesheet_view.xml',
        'views/account_analytic_line.xml',
    ],
}
