# -*- coding: utf-8 -*-

{
    'name': "Additional infos in mail message notifications",
    'version': '11.0.1.0',
    'depends': [
        'base',
        'mail'
    ],
    'author': "ABAKUS IT-SOLUTIONS",
    'website': "http://www.abakusitsolutions.eu",
    'category': 'Social',
    'description': """
This module adds methods in the 'mail.message' object that can be called from a mail template
to get informations like the partner's name from any object in Odoo (if the field exists).

To have it in the mail, you have to add a called for this method and HTML code to print it.
Example (added in the mail template for message discussion):
Customer name: ${object.get_partner_name()}

This module has been developed by ABAKUS IT-SOLUTIONS""",
    'data': [
        'data/email_templates.xml'
    ],
}