# -*- coding: utf-8 -*-

{
    'version': '11.0.1.0',
    'author': "ABAKUS IT-SOLUTIONS",
    'website': "http://www.abakusitsolutions.eu",
    'category': 'Human resources',
    "name": "Human resources AbAKUS improvements",
    "description": """
This module adds a some improvements for the HR module.
It adds:
- a date field for the entry of the employee in the company
- info regarding the key of the buidling and badge access
- info regarding the computer of the employee
- info regarding the fuel card of the employee
- note

This module has been developed by ABAKUS IT-SOLUTIONS
 """,
    "depends": [
        "hr",
    ],
    "data": [
        "views/hr_employee.xml",
    ],
    'installable': True
}
