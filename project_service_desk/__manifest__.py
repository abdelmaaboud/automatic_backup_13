# -*- coding: utf-8 -*-

{
    'name': "ABAKUS Project Service Desk",
    'version': '11.0.1.0',
    'depends': [
        'account_analytic_account_improvements',
        'project_task_mastertype',
        'hr_analytic_timesheet_improvements',
        'project_generic_close_stage',
        'project_forecast',
        'hr_holidays',
        'project_type',
    ],
    'author': "ABAKUS IT-SOLUTIONS",
    'website': "http://www.abakusitsolutions.eu",
    'category': 'Project',
    'data': [
        'views/service_view.xml',
        'views/service_project_task_view.xml',
        'views/service_project_timesheet_view.xml',
        'views/service_project_project_view.xml',
        'views/service_calendar_event_view.xml',
        'views/res_users_view.xml',
    ],
}
