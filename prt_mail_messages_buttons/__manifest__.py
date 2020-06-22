# -*- coding: utf-8 -*-
{
    'name': 'Mail Messages Buttons.'
            ' Move buttons on Mail Message Form to header',
    'version': '11.0.1.3',
    'summary': """Optional extension for free 'Mail Messages Easy' app""",
    'author': 'Ivan Sokolov',
    'category': 'Social',
    'license': 'GPL-3',
    'website': 'https://demo.promintek.com',
    'description': """
Mail Messages
""",
    'depends': ['prt_mail_messages'],
    'images': ['static/description/banner_buttons.png'],
    'data': [
        'views/prt_mail_buttons.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}
