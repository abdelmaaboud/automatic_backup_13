{
    'name': "Timesheet Report Printing",
    'category': "HR",
    'version': "11.0.1.0",
    "author": "ABAKUS IT-SOLUTIONS",
    'website': "http://www.abakusitsolutions.eu",
    'depends': [
        'hr_timesheet',
        'hr_timesheet_sheet',
        'portal_consultant'
    ],

    'data': [
        'report/hr_timesheet_report.xml',
        'views/portal_my_timesheets_templates.xml',
    ],
    'installable': True,
}