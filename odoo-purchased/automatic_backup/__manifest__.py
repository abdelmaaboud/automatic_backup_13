# -*- coding: utf-8 -*-
{
    'name': 'Automatic Backup (Odoo 9)',
    'version': '1.2.0',
    'summary': 'Automatic Backup (Odoo 9)',
    'author': 'Grzegorz Krukar (grzegorzgk1@gmail.com)',
    'description': """
    Automatic Backup (Odoo 9)
    """,
    'data': [
        'data/data.xml',
        'views/automatic_backup.xml',
        'security/security.xml'
    ],
    'depends': [
        'mail',
    ],
    'installable': True,
    'application': True,
    'price': 10.00,
    'currency': 'EUR',
}

#### HISTORY ####

# VERSION - 1.2.0 [2017-05-28]
# Google Drive Support

# VERSION - 1.1.8 [2017-05-23]
# Added option to change backup filename

# VERSION - 1.1.7 [2017-05-23]
# Fixed cron argument in Odoo 8

# VERSION - 1.1.6 [2017-05-18]
# Support for Dropbox Python Package v7.3.0

# VERSION - 1.1.5 [2017-05-11]
# Better filename validation

# VERSION - 1.1.4 [2017-05-10]
# Showing inactive backup rules

# VERSION - 1.1.3 [2017-05-10]
# Fixed bug with creating FTP backup on Windows

# VERSION - 1.1.2 [2017-05-09]
# Fixed bug with creating backup on Windows 

# VERSION - 1.1.1 [2017-05-04]
# Windows-friendly backups

# VERSION - 1.1.0 [2017-05-03]
# Added backup via DropBox

# VERSION - 1.0.1 [2017-05-01]
# Fixed bug with ignoring delete_old_backups False flag

# VERSION - 1.0.0 [2017-05-01]
# Initial release
