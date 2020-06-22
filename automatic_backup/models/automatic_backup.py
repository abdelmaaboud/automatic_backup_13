# -*- coding: utf-8 -*-

import odoo
import ftplib
import os
import re
import pickle
import tempfile
import base64
import mimetypes

from os import listdir
from os.path import isfile, join
from odoo import fields, models, api, exceptions
from odoo.tools.translate import _
from datetime import datetime
from datetime import date, timedelta

backup_pattern = '.*_\d\d\d\d-\d\d-\d\d \d\d_\d\d_\d\d.(zip|dump)$'

no_dropbox = False
try:
    import dropbox
except ImportError:
    no_dropbox = True

no_pydrive = False
try:
    from pydrive.auth import GoogleAuth
    from pydrive.drive import GoogleDrive
    from pydrive.files import GoogleDriveFile

    def SetContentFile2(self, content, filename):
        self.content = content
        if self.get('title') is None:
            self['title'] = filename
        if self.get('mimeType') is None:
            self['mimeType'] = mimetypes.guess_type(filename)[0]

    GoogleDriveFile.SetContentFile2 = SetContentFile2

except ImportError:
    no_pydrive = True

no_pysftp = False
try:
    import pysftp
except ImportError:
    no_pysftp = True

no_boto3 = False
try:
    import boto3
except ImportError:
    no_boto3 = True


class AutomaticBackup(models.Model):

    _name = 'automatic.backup'
    _description = 'Automatic Backup'
    _inherit = ['mail.thread']

    name = fields.Char(default='Automatic Backup')
    automatic_backup_rule_ids = fields.One2many('ir.cron', 'automatic_backup_id', string='Automatic Backup Rule')
    successful_backup_notify_emails = fields.Char(string='Successful Backup Notification')
    failed_backup_notify_emails = fields.Char(string='Failed Backup Notification')
    delete_old_backups = fields.Boolean(default=False)

    def default_filename(self):
        return self.env.cr.dbname

    filename = fields.Char(default=default_filename)

    @api.one
    @api.constrains('delete_days')
    def constrains_delete_days(self):
        if self.delete_old_backups:
            if self.delete_days is False or self.delete_days < 1:
                raise exceptions.ValidationError(_('Minimal Delete Days = 1'))

    delete_days = fields.Integer(string='Delete backups older than [days]', default=30)


class Cron(models.Model):

    _inherit = 'ir.cron'

    @api.model
    def create(self, vals):
        if 'dropbox_authorize_url_rel' in vals:
            vals['dropbox_authorize_url'] = vals['dropbox_authorize_url_rel']
        if 'backup_type' in vals:
            vals['name'] = 'Backup ' + vals['backup_type'] + ' ' + vals['backup_destination']
            vals['numbercall'] = -1
            vals['state'] = 'code'
            vals['code'] = ''
            vals['model_id'] = self.env['ir.model'].search([('model', '=', 'ir.cron')]).id
        output = super(Cron, self).create(vals)
        if 'backup_type' in vals:
            output.code = 'env[\'ir.cron\'].database_backup_cron_action(' + str(output.id) + ')'
        return output

    @api.one
    def write(self, vals):
        if 'dropbox_authorize_url_rel' in vals:
            vals['dropbox_authorize_url'] = vals['dropbox_authorize_url_rel']
        return super(Cron, self).write(vals)

    @api.one
    def unlink(self):
        # delete flow/auth files
        self.env['ir.attachment'].browse(self.dropbox_flow).unlink()
        output = super(Cron, self).unlink()
        return output

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if 'backup_rule' in self.env.context:
            args += ['|', ('active', '=', True), ('active', '=', False)]
        return super(Cron, self).search(args, offset, limit, order, count=count)

    @api.one
    @api.constrains('backup_type', 'backup_destination')
    def create_name(self):
        self.name = 'Backup ' + self.backup_type + ' ' + self.backup_destination

    @api.onchange('backup_destination')
    def onchange_backup_destination(self):
        if self.backup_destination == 'ftp':
            self.ftp_port = 21

        if self.backup_destination == 'sftp':
            self.ftp_port = 22
            if no_pysftp:
                raise exceptions.Warning(_('Missing required pysftp python package\n'
                                           'https://pypi.python.org/pypi/pysftp'))

        if self.backup_destination == 'dropbox':
            if no_dropbox:
                raise exceptions.Warning(_('Missing required dropbox python package\n'
                                           'https://pypi.python.org/pypi/dropbox'))
            flow = dropbox.DropboxOAuth2FlowNoRedirect('jqurrm8ot7hmvzh', '7u0goz5nmkgr1ot')
            self.dropbox_authorize_url = flow.start()
            self.dropbox_authorize_url_rel = self.dropbox_authorize_url

            self.dropbox_flow = self.env['ir.attachment'].create(dict(
                datas=base64.b64encode(pickle.dumps(flow)),
                name='dropbox_flow',
                datas_fname='dropbox_flow',
                description='Automatic Backup File'
            )).id

        if self.backup_destination == 'google_drive':
            if no_pydrive:
                raise exceptions.Warning(_('Missing required PyDrive python package\n'
                                           'https://pypi.python.org/pypi/PyDrive'))
            secrets_path = os.path.dirname(
                os.path.realpath(__file__)) + os.sep + '..' + os.sep + 'data' + os.sep + 'client_secrets.json'
            GoogleAuth.DEFAULT_SETTINGS['client_config_file'] = secrets_path
            gauth = GoogleAuth()
            self.dropbox_authorize_url = gauth.GetAuthUrl()
            self.dropbox_authorize_url_rel = self.dropbox_authorize_url
            self.dropbox_flow = self.dropbox_flow = self.env['ir.attachment'].create(dict(
                datas=base64.b64encode(pickle.dumps(gauth)),
                name='dropbox_flow',
                datas_fname='dropbox_flow',
                description='Automatic Backup File'
            )).id

    @api.one
    @api.constrains('backup_destination', 'dropbox_authorization_code', 'dropbox_flow')
    def constrains_dropbox(self):
        if self.backup_destination == 'sftp':
            if no_pysftp:
                raise exceptions.Warning(_('Missing required pysftp python package\n'
                                           'https://pypi.python.org/pypi/pysftp'))

        if self.backup_destination == 'dropbox':
            if no_dropbox:
                raise exceptions.Warning(_('Missing required dropbox python package\n'
                                           'https://pypi.python.org/pypi/dropbox'))

            ia = self.env['ir.attachment'].browse(self.dropbox_flow)
            ia.res_model = 'ir.cron'
            ia.res_id = self.id

            flow = pickle.loads(base64.b64decode(ia.datas))
            result = flow.finish(self.dropbox_authorization_code.strip())
            self.dropbox_access_token = result.access_token
            self.dropbox_user_id = result.user_id

        if self.backup_destination == 'google_drive':
            if no_pydrive:
                raise exceptions.Warning(_('Missing required PyDrive python package\n'
                                           'https://pypi.python.org/pypi/PyDrive'))

            ia = self.env['ir.attachment'].browse(self.dropbox_flow)
            ia.res_model = 'ir.cron'
            ia.res_id = self.id
            gauth = pickle.loads(base64.b64decode(ia.datas))
            gauth.Auth(self.dropbox_authorization_code)
            ia.datas = base64.b64encode(pickle.dumps(gauth))

        if self.backup_destination == 's3':
            if no_boto3:
                raise exceptions.Warning(_('Missing required boto3 python package\n'
                                           'https://pypi.python.org/pypi/boto3'))

    @api.one
    def check_settings(self):
        self.create_backup(True)

    @api.one
    def backup_btn(self):
        self.create_backup()

    def get_selection_field_value(self, field, key):
        my_model_obj = self
        return dict(my_model_obj.fields_get(allfields=[field])[field]['selection'])[key]

    @api.multi
    def show_rule_form(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Backup Rule',
            'res_model': 'ir.cron',
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }

    def create_backup(self, check=False):
        filename = ''
        if check is False:
            backup_binary = odoo.service.db.dump_db(self.env.cr.dbname, None, self.backup_type)
        else:
            backup_binary = tempfile.TemporaryFile()
            backup_binary.write(str.encode('Dummy File'))
            backup_binary.seek(0)

        # delete unused flow/auth files
        self.env['ir.attachment'].search([('description', '=', 'Automatic Backup File'), ('res_id', '=', False)]).unlink()

        if self.backup_destination == 'folder':
            filename = self.folder_path + os.sep + self.automatic_backup_id.filename + '_' + \
                       str(datetime.now()).split('.')[0].replace(':', '_') + '.' + self.backup_type
            file_ = open(filename, 'wb')
            file_.write(backup_binary.read())
            file_.close()
            if check is True:
                os.remove(filename)
            if self.automatic_backup_id.delete_old_backups:
                files = [f for f in listdir(self.folder_path) if isfile(join(self.folder_path, f))]
                for backup in files:
                    if re.match(backup_pattern, backup) is not None:
                        px = len(backup) - 24
                        if backup.endswith('.dump'):
                            px -= 1
                        filedate = date(int(backup[px+1:px+5]), int(backup[px+6:px+8]), int(backup[px+9:px+11]))
                        if filedate + timedelta(days=self.automatic_backup_id.delete_days) < date.today():
                            os.remove(self.folder_path + os.sep + backup)
                            self.file_delete_message(backup)

        if self.backup_destination == 'ftp':
            filename = self.automatic_backup_id.filename + '_' + str(datetime.now()).split('.')[0].replace(':', '_') \
                       + '.' + self.backup_type
            ftp = ftplib.FTP()
            ftp.connect(self.ftp_address, self.ftp_port)
            ftp.login(self.ftp_login, self.ftp_password)
            ftp.cwd(self.ftp_path)
            ftp.storbinary('STOR ' + filename, backup_binary)
            if check is True:
                ftp.delete(filename)
            if self.automatic_backup_id.delete_old_backups:
                for backup in ftp.nlst():
                    if re.match(backup_pattern, backup) is not None:
                        px = len(backup) - 24
                        if backup.endswith('.dump'):
                            px -= 1
                        filedate = date(int(backup[px + 1:px + 5]), int(backup[px + 6:px + 8]), int(backup[px + 9:px + 11]))
                        if filedate + timedelta(days=self.automatic_backup_id.delete_days) < date.today():
                            ftp.delete(backup)
                            self.file_delete_message(backup)

        if self.backup_destination == 'sftp':
            filename = self.automatic_backup_id.filename + '_' + str(datetime.now()).split('.')[0].replace(':', '_') \
                       + '.' + self.backup_type

            cnopts = pysftp.CnOpts()
            cnopts.hostkeys = None
            sftp = pysftp.Connection(self.ftp_address, username=self.ftp_login, password=self.ftp_password,
                                     cnopts=cnopts, port=self.ftp_port)
            sftp.putfo(backup_binary, self.ftp_path + '/' + filename)
            if check is True:
                sftp.remove(self.ftp_path + '/' + filename)
            if self.automatic_backup_id.delete_old_backups:
                for backup in sftp.listdir(self.ftp_path):
                    if re.match(backup_pattern, backup) is not None:
                        px = len(backup) - 24
                        if backup.endswith('.dump'):
                            px -= 1
                        filedate = date(int(backup[px + 1:px + 5]), int(backup[px + 6:px + 8]),
                                        int(backup[px + 9:px + 11]))
                        if filedate + timedelta(days=self.automatic_backup_id.delete_days) < date.today():
                            sftp.remove(self.ftp_path + '/' + backup)
                            self.file_delete_message(backup)

        if self.backup_destination == 'dropbox':
            filename = self.automatic_backup_id.filename + '_' + str(datetime.now()).split('.')[0].replace(':', '_') \
                       + '.' + self.backup_type
            client = dropbox.Dropbox(self.dropbox_access_token)
            client.files_upload(backup_binary.read(), '/' + filename)
            if check is True:
                client.files_delete_v2('/' + filename)
            if self.automatic_backup_id.delete_old_backups:
                for f in client.files_list_folder('').entries:
                    if re.match(backup_pattern, f.name) is not None:
                        px = len(f.name) - 24
                        if f.name.endswith('.dump'):
                            px -= 1
                        filedate = date(int(f.name[px + 1:px + 5]), int(f.name[px + 6:px + 8]), int(f.name[px + 9:px + 11]))
                        if filedate + timedelta(days=self.automatic_backup_id.delete_days) < date.today():
                            client.files_delete_v2('/' + f.name)
                            self.file_delete_message(f.name[1:])

        if self.backup_destination == 'google_drive':
            filename = self.automatic_backup_id.filename + '_' + str(datetime.now()).split('.')[0].replace(':', '_') \
                       + '.' + self.backup_type

            ia = self.env['ir.attachment'].browse(self.dropbox_flow)
            gauth = pickle.loads(base64.b64decode(ia.datas))
            drive = GoogleDrive(gauth)

            def getFolderID(folder_id, parent):
                file_list = drive.ListFile(
                    {'q': "'" + parent + "' in parents and trashed=false and mimeType='application/vnd.google-apps.folder'"
                          "and title='" + folder_id + "'"}).GetList()
                for file1 in file_list:
                    if file1['title'] == folder_id:
                        return file1['id']
                folder_metadata = {'title': folder_id,
                                   'mimeType': 'application/vnd.google-apps.folder',
                                   'parents': [{'id': parent}]}
                folder = drive.CreateFile(folder_metadata)
                folder.Upload()
                return folder['id']

            def getFolderFromPath(path):
                folder_id = 'root'
                for p in path.split('/'):
                    if not p:
                        continue
                    folder_id = getFolderID(p, folder_id)
                return folder_id

            folderid = getFolderFromPath(self.dropbox_path)
            file1 = drive.CreateFile({'title': filename, 'parents': [{'kind': 'drive#fileLink', 'id': folderid}]})

            if self.backup_type == 'dump':
                # TODO: problems with to big files
                # _io.BufferedReader
                tmp_attachment = self.env['ir.attachment'].create({
                    'datas': base64.b64encode(backup_binary.read()),
                    'name': 'doc.dump',
                    'datas_fname': 'doc.dump'
                })
                file1.SetContentFile(tmp_attachment._filestore() + os.sep + tmp_attachment.store_fname)
                file1.Upload()
                tmp_attachment.unlink()
            else:
                file1.SetContentFile2(backup_binary, 'binary.zip')
                file1.Upload()

            if check is True:
                file1.Delete()
            if self.automatic_backup_id.delete_old_backups:
                file_list = drive.ListFile({'q': "'" + folderid + "' in parents and trashed=false"}).GetList()
                for gfile in file_list:
                    if re.match(backup_pattern, gfile['title']) is not None:
                        px = len(gfile['title']) - 24
                        if gfile['title'].endswith('.dump'):
                            px -= 1
                        filedate = date(int(gfile['title'][px + 1:px + 5]), int(gfile['title'][px + 6:px + 8]), int(gfile['title'][px + 9:px + 11]))
                        if filedate + timedelta(days=self.automatic_backup_id.delete_days) < date.today():
                            drive.CreateFile({'id': gfile['id']}).Delete()
                            self.file_delete_message(gfile['title'])

        if self.backup_destination == 's3':
            filename = self.automatic_backup_id.filename + '_' + str(datetime.now()).split('.')[0].replace(':', '_') \
                       + '.' + self.backup_type
            s3 = boto3.resource('s3', aws_access_key_id=self.s3_access_key, aws_secret_access_key=self.s3_access_key_secret)
            s3.Bucket(self.s3_bucket_name).put_object(Key='Odoo Automatic Backup/' + filename, Body=backup_binary)
            if self.automatic_backup_id.delete_old_backups:
                for o in s3.Bucket(self.s3_bucket_name).objects.all():
                    if o.key.startswith('Odoo Automatic Backup/'):
                        px = len(o.key) - 24
                        if o.key.endswith('.dump'):
                            px -= 1
                        filedate = date(int(o.key[px + 1:px + 5]), int(o.key[px + 6:px + 8]), int(o.key[px + 9:px + 11]))
                        if filedate + timedelta(days=self.automatic_backup_id.delete_days) < date.today():
                            self.file_delete_message(o.key)
                            o.delete()

        backup_binary.close()
        if check is True:
            raise exceptions.Warning(_('Settings are correct.'))
        self.success_message(filename)

    def success_message(self, filename):
        msg = _('Backup created successfully!') + '<br/>'
        msg += _('Backup Type: ') + self.get_selection_field_value('backup_type', self.backup_type) + '<br/>'
        msg += _('Backup Destination: ') + self.get_selection_field_value('backup_destination',
                                                                          self.backup_destination) + '<br/>'
        if self.backup_destination == 'folder':
            msg += _('Folder Path: ') + self.folder_path + '<br/>'
        if self.backup_destination == 'ftp':
            msg += _('FTP Adress: ') + self.ftp_address + '<br/>'
            msg += _('FTP Path: ') + self.ftp_path + '<br/>'
        msg += _('Filename: ') + filename + '<br/>'
        self.env['mail.message'].create(dict(
            subject=_('Backup created successfully!'),
            body=msg,
            email_from=self.env['res.users'].browse(self.env.uid).email,
            model='automatic.backup',
            res_id=self.automatic_backup_id.id,
        ))
        if self.automatic_backup_id.successful_backup_notify_emails:
            self.env['mail.mail'].create(dict(
                subject=_('Backup created successfully!'),
                body_html=msg,
                email_from=self.env['res.users'].browse(self.env.uid).email,
                email_to=self.automatic_backup_id.successful_backup_notify_emails,
            )).send()

    def file_delete_message(self, filename):
        msg = _('Old backup deleted!') + '<br/>'
        msg += _('Backup Type: ') + self.get_selection_field_value('backup_type', self.backup_type) + '<br/>'
        msg += _('Backup Destination: ') + self.get_selection_field_value('backup_destination',
                                                                          self.backup_destination) + '<br/>'
        if self.backup_destination == 'folder':
            msg += _('Folder Path: ') + self.folder_path + '<br/>'
        if self.backup_destination == 'ftp':
            msg += _('FTP Adress: ') + self.ftp_address + '<br/>'
            msg += _('FTP Path: ') + self.ftp_path + '<br/>'
        msg += _('Filename: ') + filename + '<br/>'
        self.env['mail.message'].create(dict(
            subject=_('Old backup deleted!'),
            body=msg,
            email_from=self.env['res.users'].browse(self.env.uid).email,
            model='automatic.backup',
            res_id=self.automatic_backup_id.id,
        ))
        if self.automatic_backup_id.successful_backup_notify_emails:
            self.env['mail.mail'].create(dict(
                subject=_('Old backup deleted!'),
                body_html=msg,
                email_from=self.env['res.users'].browse(self.env.uid).email,
                email_to=self.automatic_backup_id.successful_backup_notify_emails,
            )).send()

    @api.model
    def database_backup_cron_action(self, *args):
        backup_rule = False
        try:
            if len(args) != 1 or isinstance(args[0], int) is False:
                raise exceptions.ValidationError(_('Wrong method parameters'))
            rule_id = args[0]
            backup_rule = self.browse(rule_id)
            backup_rule.create_backup()
        except Exception as e:
            msg = _('Automatic backup failed!') + '<br/>'
            msg += _('Backup Type: ') + backup_rule.get_selection_field_value('backup_type', backup_rule.backup_type) + '<br/>'
            msg += _('Backup Destination: ') + backup_rule.get_selection_field_value('backup_destination', backup_rule.backup_destination) + '<br/>'
            if backup_rule.backup_destination == 'folder':
                msg += _('Folder Path: ') + backup_rule.folder_path + '<br/>'
            if backup_rule.backup_destination == 'ftp':
                msg += _('FTP Adress: ') + backup_rule.ftp_address + '<br/>'
                msg += _('FTP Path: ') + backup_rule.ftp_path + '<br/>'
            msg += _('Exception: ') + str(e) + '<br/>'
            self.env['mail.message'].create(dict(
                subject=_('Automatic backup failed!'),
                body=msg,
                email_from=self.env['res.users'].browse(self.env.uid).email,
                model='automatic.backup',
                res_id=backup_rule.automatic_backup_id.id,
            ))
            if backup_rule.automatic_backup_id.failed_backup_notify_emails:
                self.env['mail.mail'].create(dict(
                    subject=_('Automatic backup failed!'),
                    body_html=msg,
                    email_from=self.env['res.users'].browse(self.env.uid).email,
                    email_to=backup_rule.automatic_backup_id.failed_backup_notify_emails,
                )).send()

    automatic_backup_id = fields.Many2one('automatic.backup')
    backup_type = fields.Selection([('dump', 'Database Only'),
                                    ('zip', 'Database and Filestore')],
                                   string='Backup Type')
    backup_destination = fields.Selection([('folder', 'Folder'),
                                           ('ftp', 'FTP'),
                                           ('sftp', 'SFTP'),
                                           ('dropbox', 'Dropbox'),
                                           ('google_drive', 'Google Drive'),
                                           ('s3', 'Amazon S3')],
                                          string='Backup Destionation')
    folder_path = fields.Char(string='Folder Path')
    ftp_address = fields.Char(string='URL')
    ftp_port = fields.Integer(string='Port')
    ftp_login = fields.Char(string='Login')
    ftp_password = fields.Char(string='Password')
    ftp_path = fields.Char(string='Path')
    dropbox_authorize_url = fields.Char(string='Authorize URL')
    dropbox_authorize_url_rel = fields.Char()
    dropbox_authorization_code = fields.Char(string='Authorization Code')
    dropbox_flow = fields.Integer()
    dropbox_access_token = fields.Char()
    dropbox_user_id = fields.Char()
    dropbox_path = fields.Char(default='/Odoo Automatic Backups/', string='Backup Path')
    s3_bucket_name = fields.Char(string='Bucket name')
    s3_username = fields.Char(string='Username')
    s3_access_key = fields.Char(string='Access key')
    s3_access_key_secret = fields.Char(string='Acces key secret')
