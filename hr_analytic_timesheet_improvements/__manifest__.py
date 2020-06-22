{
    'name': "Worklog management improvements",
    'version': '11.0.1.0',
    'depends': [
        'hr_timesheet',
        'project',
        'timesheet_grid',
        'project_generic_close_stage',
        'contract_timesheet_activities_on_site_management',
    ],
    'author': "ABAKUS IT-SOLUTIONS",
    'website': "http://www.abakusitsolutions.eu",
    'category': 'Human Resources',
    'data': [
        'views/hr_analytic_timesheet_view.xml',
        'views/project_task_view.xml',

        'data/hr_analytic_timesheet_data.xml',
    ],
}
