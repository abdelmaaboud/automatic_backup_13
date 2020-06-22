# -*- coding: utf-8 -*-

{
    'version': '11.0.1.0',
    'author': "ABAKUS IT-SOLUTIONS",
    'website': "http://www.abakusitsolutions.eu",
    'category': 'Human resources',
    "name": "HR applicants country",
    "description": """
This module adds a some improvements for the HR recruitment module.
It adds:
- a field with all selectable countries on hr.applicant
- a field to check if the country is usable on the field for hr.applicant

This module has been developed by ABAKUS IT-SOLUTIONS
 """,
    "depends": [
        "base",
        "hr",
        "hr_recruitment",
    ],
    "data": [
        "views/hr_applicant.xml",
        "views/res_country.xml"
    ],
    'installable': True
}
