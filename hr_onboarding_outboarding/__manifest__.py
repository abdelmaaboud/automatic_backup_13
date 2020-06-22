# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
{
    'name': "Employee Onboarding and Outboarding",
    'version': '11.0.1.0',
    'license': 'AGPL-3',
    'depends': [
        'hr',
        'project',
    ],
    'author': "ABAKUS IT-SOLUTIONS",
    'website': "http://www.abakusitsolutions.eu",
    'category': 'Human Resources',
    'data': [
        'views/hr_employee_view.xml',
        'views/project_project_view.xml',
        'views/hr_on_out_boarding_project_view.xml',
        'security/ir.model.access.csv',
    ],
}
