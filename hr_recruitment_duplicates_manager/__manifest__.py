{
    'name': "HR Recruitment Duplicates Manager",
    'version': '11.0.1.0',
    'depends': [
        'hr_recruitment',
    ],
    'author': "ABAKUS IT-SOLUTIONS",
    'website': "http://www.abakusitsolutions.eu/",
    'category': 'Recruitment',
    'data': [
        'views/hr_applicant_view.xml',
        'wizards/hr_duplicate_check_wizard.xml',
        'views/hr_duplicate_suspects_view.xml',

        'security/ir.model.access.csv',
    ]
}
