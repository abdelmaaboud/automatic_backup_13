# -*- coding: utf-8 -*-

{
    'name': "Close Tasks and Issues from list",
    'version': '11.0.1.0',
    'depends': [
        'project',
        'project_task_mastertype'
    ],
    'author': "ABAKUS IT-SOLUTIONS",
    'website': "http://www.abakusitsolutions.eu",
    'category': 'Project',
    'data': [
        'wizard/project_close_task_issue_from_list_wizard.xml',
        'security/ir.model.access.csv'
    ],
}