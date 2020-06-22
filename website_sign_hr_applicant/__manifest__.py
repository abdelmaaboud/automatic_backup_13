# -*- coding: utf-8 -*-
{
    'name': "Document Signing linked to HR Applicant",

    'summary': """
    """,

    'author': "ABAKUS IT-SOLUTIONS",
    'website': "http://www.abakusitsolutions.eu",

    'category': 'Document Management',
    'version': '11.0.1.0',

    'depends': [
        'website_sign',
        'hr_recruitment',
    ],

    'data': [
        'wizard/applicant_send_document_sign_wizard_view.xml',
        'views/hr_applicant_view.xml',
        'views/signature_request_template_view.xml',
        'views/signature_request_view.xml',
        'views/signature_request_item_view.xml',
    ],
}