{
    'name': "Company information banners",
    'version': '11.0.1.0',
    'depends': [
        'hr_timesheet',
        'mail',
        'hr_holidays',
        'hr_expense',
        'timesheet_grid',
        'hr_timesheet_sheet',
    ],
    'author': "ABAKUS IT-SOLUTIONS",
    'website': "http://www.abakusitsolutions.eu",
    'category': 'Social',
    'data': [
        'views/social_banners.xml',
        'views/hr_timesheet.xml',
        'views/hr_expense.xml',
        'views/hr_holiday.xml',
        'security/ir.model.access.csv',
    ],
}

