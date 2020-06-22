# -*- coding: utf-8 -*-
{
    'name': 'Automatic Backup (Dropbox, Google Drive, Amazon S3, SFTP)',
    'version': '1.5.2',
    'summary': 'Automatic Backup',
    'author': 'Grzegorz Krukar (grzegorzgk1@gmail.com)',
    'description': """
    Automatic Backup
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
    'price': 20.00,
    'currency': 'EUR',
}

#### HISTORY ####

# VERSION - 1.5.2 [2018-05-13]
# Fix issue with Google Drive dump and zip files sending using different method

# VERSION - 1.5.1 [2018-05-08]
# Fix issue with Google Drive database only backup

# VERSION - 1.5.0 [2018-01-26]
# Added support for Amazon S3

# VERSION - 1.4.5 [2018-01-26]
# Fixed compatibility issue with Google Drive and Windows

# VERSION - 1.4.4 [2018-01-24]
# Fix typo

# VERSION - 1.4.3 [2018-01-18]
# Name change

# VERSION - 1.4.2 [2017-12-16]
# Support for custom Google Drive backup path

# VERSION - 1.4.1 [2017-12-01]
# Updated ir.model search to new odoo version

# VERSION - 1.4.0 [2017-11-04]
# Added support for backup via SFTP

# VERSION - 1.3.1 [2017-10-29]
# Storing flow/auth files in Odoo filestore instead of database or Odoo folder

# VERSION - 1.3.0 [2017-10-15]
# Updated to Dropbox API v2

# VERSION - 1.2.5 [2017-08-15]
# Removed testing information

# VERSION - 1.2.4 [2017-07-27]
# Added testing information

# VERSION - 1.2.3 [2017-07-26]
# Specify required dropbox python package version, compatibility issues with the newest one

# VERSION - 1.2.2 [2017-07-25]
# Fixed: Error with finding date in existing backups

# VERSION - 1.2.1 [2017-07-09]
# Fixed: writing args to other cron jobs

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
