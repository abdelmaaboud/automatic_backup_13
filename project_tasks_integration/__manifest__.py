# -*- coding: utf-8 -*-

{
    'name': "ABAKUS Project Tasks Integration",
    'version': '11.0.1.0',
    'depends': [
        'project',
        'project_type',
        'project_task_mastertype',
    ],
    'author': "ABAKUS IT-SOLUTIONS",
    'website': "http://www.abakusitsolutions.eu",
    'category': 'Project',
    'data': [
        'views/project_task_view.xml',
        'views/project_project_view.xml',
        'views/project_task_type.xml',
        'views/project_task_mastertype.xml',

        'data/ir_actions_server_data.xml',
        'data/project_issue_email_template.xml',
    ],
}
