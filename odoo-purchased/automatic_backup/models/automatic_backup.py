# -*- coding: utf-8 -*-

import odoo
import ftplib
import os
import re
import pickle
from io import StringIO
import tempfile

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
except ImportError:
    no_pydrive = True


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
            vals['model'] = 'ir.cron'
            vals['function'] = 'database_backup_cron_action'
        output = super(Cron, self).create(vals)
        output.args = ({'id': output.id},)
        return output

    @api.one
    def write(self, vals):
        if 'dropbox_authorize_url_rel' in vals:
            vals['dropbox_authorize_url'] = vals['dropbox_authorize_url_rel']
        return super(Cron, self).write(vals)

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
        if self.backup_destination == 'dropbox':
            if no_dropbox:
                raise exceptions.Warning(_('Missing required dropbox python package\n'
                                           'https://pypi.python.org/pypi/dropbox'))
            flow = dropbox.DropboxOAuth2FlowNoRedirect('jqurrm8ot7hmvzh', '7u0goz5nmkgr1ot')
            self.dropbox_authorize_url = flow.start()
            self.dropbox_authorize_url_rel = self.dropbox_authorize_url
            self.dropbox_flow = pickle.dumps(flow)
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
            self.dropbox_flow = pickle.dumps(gauth)

    @api.one
    @api.constrains('backup_destination', 'dropbox_authorization_code', 'dropbox_flow')
    def constrains_dropbox(self):
        if self.backup_destination == 'dropbox':
            if no_dropbox:
                raise exceptions.Warning(_('Missing required dropbox python package\n'
                                           'https://pypi.python.org/pypi/dropbox'))
            flow = pickle.loads(self.dropbox_flow)
            result = flow.finish(self.dropbox_authorization_code.strip())
            if isinstance(result, tuple):
                # dropbox python package old version
                self.dropbox_access_token, self.dropbox_user_id = result
            else:
                # dropbox python package new version
                self.dropbox_access_token = result.access_token
                self.dropbox_user_id = result.user_id
        if self.backup_destination == 'google_drive':
            if no_pydrive:
                raise exceptions.Warning(_('Missing required PyDrive python package\n'
                                           'https://pypi.python.org/pypi/PyDrive'))
            gauth = pickle.loads(self.dropbox_flow)
            gauth.Auth(self.dropbox_authorization_code)
            self.google_auth = pickle.dumps(gauth)

    automatic_backup_id = fields.Many2one('automatic.backup')

    backup_type = fields.Selection([('dump', 'Database Only'),
                                    ('zip', 'Database and Filestore')],
                                   string='Backup Type')
    backup_destination = fields.Selection([('folder', 'Folder'),
                                           ('ftp', 'FTP'),
                                           ('dropbox', 'Dropbox'),
                                           ('google_drive', 'Google Drive')],
                                          string='Backup Destionation')

    folder_path = fields.Char(string='Folder Path')

    ftp_address = fields.Char(string='FTP Adress')
    ftp_port = fields.Integer(string='FTP Port', default=21)
    ftp_login = fields.Char(string='FTP Login')
    ftp_password = fields.Char(string='FTP Password')
    ftp_path = fields.Char(string='FTP Path')

    dropbox_authorize_url = fields.Char(string='Authorize URL')
    dropbox_authorize_url_rel = fields.Char()
    dropbox_authorization_code = fields.Char(string='Authorization Code')
    dropbox_flow = fields.Text()
    dropbox_access_token = fields.Char()
    dropbox_user_id = fields.Char()

    google_auth = fields.Char()

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
            backup_binary = StringIO.StringIO()
            backup_binary.write('Dummy File')
            backup_binary.seek(0)
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
                        px = len(backup.split('_')[0])
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
                        px = len(backup.split('_')[0])
                        filedate = date(int(backup[px + 1:px + 5]), int(backup[px + 6:px + 8]), int(backup[px + 9:px + 11]))
                        if filedate + timedelta(days=self.automatic_backup_id.delete_days) < date.today():
                            ftp.delete(backup)
                            self.file_delete_message(backup)
        if self.backup_destination == 'dropbox':
            filename = self.automatic_backup_id.filename + '_' + str(datetime.now()).split('.')[0].replace(':', '_') \
                       + '.' + self.backup_type
            client = dropbox.client.DropboxClient(self.dropbox_access_token)
            client.put_file('/' + filename, backup_binary)
            if check is True:
                client.file_delete('/' + filename)
            if self.automatic_backup_id.delete_old_backups:
                folder = client.metadata('/')
                for f in folder['contents']:
                    if f['is_dir'] is True:
                        continue
                    if re.match(backup_pattern, f['path']) is not None:
                        px = len(f['path'].split('_')[0])
                        filedate = date(int(f['path'][px + 1:px + 5]), int(f['path'][px + 6:px + 8]), int(f['path'][px + 9:px + 11]))
                        if filedate + timedelta(days=self.automatic_backup_id.delete_days) < date.today():
                            client.file_delete(f['path'])
                            self.file_delete_message(f['path'][1:])
        if self.backup_destination == 'google_drive':
            filename = self.automatic_backup_id.filename + '_' + str(datetime.now()).split('.')[0].replace(':', '_') \
                       + '.' + self.backup_type
            gauth = pickle.loads(self.google_auth)
            drive = GoogleDrive(gauth)

            def getFolderID():
                file_list = drive.ListFile({'q': "'root' in parents and trashed=false and mimeType='application/vnd.google-apps.folder'"
                                                 "and title='Odoo Automatic Backups'"}).GetList()
                for file1 in file_list:
                    if file1['title'] == 'Odoo Automatic Backups':
                        return file1['id']
                folder_metadata = {'title': 'Odoo Automatic Backups', 'mimeType': 'application/vnd.google-apps.folder'}
                folder = drive.CreateFile(folder_metadata)
                folder.Upload()
                return folder['id']

            folderid = getFolderID()

            tf = tempfile.NamedTemporaryFile()
            tf.write(backup_binary.read())
            tf.seek(0)
            file1 = drive.CreateFile({'title': filename, 'parents': [{'kind': 'drive#fileLink', 'id': folderid}]})
            file1.SetContentFile(tf.name)
            file1.Upload()
            tf.close()
            if check is True:
                file1.Delete()
            if self.automatic_backup_id.delete_old_backups:
                file_list = drive.ListFile({'q': "'" + folderid + "' in parents and trashed=false"}).GetList()
                for gfile in file_list:
                    if re.match(backup_pattern, gfile['title']) is not None:
                        px = len(gfile['title'].split('_')[0])
                        filedate = date(int(gfile['title'][px + 1:px + 5]), int(gfile['title'][px + 6:px + 8]), int(gfile['title'][px + 9:px + 11]))
                        if filedate + timedelta(days=self.automatic_backup_id.delete_days) < date.today():
                            drive.CreateFile({'id': gfile['id']}).Delete()
                            self.file_delete_message(gfile['title'])

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
    def database_backup_cron_action(self, args):
        backup_rule = False
        try:
            if len(args) != 1 or isinstance(args['id'], int) is False:
                raise exceptions.ValidationError(_('Wrong method parameters'))
            rule_id = args['id']
            backup_rule = self.browse(rule_id)
            backup_rule.create_backup()
        except Exception:
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
