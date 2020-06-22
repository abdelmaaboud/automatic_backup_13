# -*- coding: utf-8 -*-
{
    'name': "HR Holidays Summary Report Improved",
    'summary': """""",
    'author': "ABAKUS IT-SOLUTIONS",
    'website': "http://www.abakusitsolutions.eu",

    'category': 'Human Resources',
    'version': '11.0.1.0',

    'depends': [
        'hr',
        'hr_holidays',
    ],

    'data': [
        'views/hr_holidays_status.xml',
        'views/hr_holidays_summary_dept.xml',
        'templates/report_hr_holidays_summary.xml'
    ],
}