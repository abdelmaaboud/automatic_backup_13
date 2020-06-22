from odoo import models, fields, api, http, _
import requests
from datetime import datetime
import json
import logging
from odoo.http import request

_logger = logging.getLogger(__name__)


class Office365(models.Model):
    _inherit = "res.users"

    ks_is_login_user = fields.Boolean(compute='ks_is_current_user')
    ks_code = fields.Char("Code")
    ks_scope = fields.Char("Scope")
    ks_auth_token = fields.Char("Authorization Token", store=True)
    ks_auth_refresh_token = fields.Char("Refresh Token", store=True)
    ks_auth_user_name = fields.Char("Username", readonly=True)
    ks_auth_user_email = fields.Char("Email", readonly=True)

    def ks_is_job_completed(self, ks_job, ks_module):
        ks_previous_job = self.env["ks.office.job"].search([('ks_records', '>=', 0),
                                                            ('ks_status', '=', 'error'),
                                                            ('ks_module', '=', ks_module),
                                                            ('create_uid', '=', self.id)], limit=1)
        is_ks_process_running = self.env["ks.office.job"].search([('ks_records', '>=', 0),
                                                                  ('ks_status', '=', 'in_process'),
                                                                  ('ks_module', '=', ks_module),
                                                                  ('create_uid', '=', self.id)])

        if is_ks_process_running:
            return False
        elif ks_previous_job and ks_previous_job[0].ks_job == ks_job:
            return ks_previous_job[0]
        else:
            return self.env["ks.office.job"].create({'ks_status': 'in_process',
                                                     'ks_module': ks_module,
                                                     'ks_job': ks_job})

    def open_current_user(self):
        return {
            'name': 'User form',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'res.users',
            'view_id': self.env.ref('ks_office365_base.ks_office365_main_form').id,
            'res_id': self.env.user.id,
            'context': {
                'default_form_view_ref': 'ks_office365_base.ks_office365_view_users_form'
            }
        }

    def get_authentication_code(self):
        ks_current_datatime = datetime.today()

        ks_admin = self.env['ks_office365.settings'].sudo().search([], limit=1)
        ks_client_id = ks_admin.ks_client_id
        ks_client_secret = ks_admin.ks_client_secret
        ks_redirect_url = ks_admin.ks_redirect_url
        ks_computed_scope = self.get_scope()

        if type(ks_computed_scope) is dict:
            return ks_computed_scope

        ks_scope = "offline_access " + ks_computed_scope
        self.sudo().ks_scope = ks_scope

        if not ks_client_id or not ks_client_secret or not ks_redirect_url:
            self.ks_create_log("authentication", "Authentication", "", 0, ks_current_datatime, "authentication",
                               "authentication", "failed", _("Client ID, Client Secret and Redirect URI are required"))
            return self.ks_show_error_message(_("Client ID, Client Secret or Redirect URI not entered!"))

        data = (ks_client_id, "code", ks_redirect_url, ks_scope, "query", "ks_success")
        url = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id=%s&response_type=%s" \
              "&redirect_uri=%s&scope=%s&response_mode=%s&state=%s" % data

        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': url
        }

    def ks_generate_token(self):
        ks_current_datatime = datetime.today()
        api_endpoint = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        ks_auth_user = self.sudo().env["ks_office365.settings"].search([], limit=1)
        ks_client_id = ks_auth_user.ks_client_id
        ks_client_secret = ks_auth_user.ks_client_secret
        ks_redirect_url = ks_auth_user.ks_redirect_url
        ks_scope = self.ks_scope
        ks_code = self.ks_code

        if not ks_auth_user or not ks_code:
            self.ks_create_log("authentication", "Authentication", "", 0, ks_current_datatime, "authentication",
                               "authentication", "failed", _("Access Denied! \nUser is not authenticated."))
            return self.ks_show_error_message(_("Access Denied! \nUser is not authenticated."))

        ks_data = {
            "client_id": ks_client_id,
            "client_secret": ks_client_secret,
            "redirect_uri": ks_redirect_url,
            "code": ks_code,
            "scope": ks_scope,
            "grant_type": "authorization_code",
        }
        try:
            response = requests.post(api_endpoint, data=ks_data)
        except Exception as ex:
            return self.ks_show_error_message(_("Internet connected failed!"))
        json_data = json.loads(response.text)
        if "access_token" in json_data:
            self.write({
                "ks_auth_token": json_data['token_type'] + " " + json_data['access_token'],
                "ks_auth_refresh_token": json_data['refresh_token']
            })
            self.ks_save_auth_user_details(self.ks_auth_token)
            self.ks_create_log("authentication", "Authentication", "", 0, ks_current_datatime, "authentication",
                               "authentication", "success", _("Token generated successful!"))
        else:
            self.ks_create_log("authentication", "Authentication", "", 0, ks_current_datatime, "authentication",
                               "authentication", "failed", _(json_data['error_description']))
            return self.ks_show_error_message(_("Authentication failed!\n Check log to know more"))

    def ks_clear_token(self):
        self.sudo().write({
            'ks_auth_token': False,
            'ks_auth_user_name': False,
            'ks_auth_user_email': False
        })

    # Showing user details whose token is generated
    def ks_save_auth_user_details(self, ks_auth_token):
        ks_head = {
            "Authorization": ks_auth_token,
            "Host": "graph.microsoft.com"
        }
        ks_office_auth_user = json.loads(requests.get("https://graph.microsoft.com/v1.0/me/", headers=ks_head).text)
        if 'error' not in ks_office_auth_user:
            self.write({
                'ks_auth_user_name': ks_office_auth_user['displayName'] or ks_office_auth_user['userPrincipalName'],
                'ks_auth_user_email': ks_office_auth_user['userPrincipalName']
            })
        else:
            _logger.error("Unable to fetch User's Profile \nReason: %s" % ks_office_auth_user['error'])

    def ks_login_office_user(self, ks_setting, ks_code):
        ks_client_id = ks_setting.ks_client_id
        ks_client_secret = ks_setting.ks_client_secret
        ks_redirect_url = ks_setting.ks_redirect_url
        ks_scope = "User.Read"
        ks_data = {
            "client_id": ks_client_id,
            "client_secret": ks_client_secret,
            "redirect_uri": ks_redirect_url,
            "code": ks_code,
            "scope": ks_scope,
            "grant_type": "authorization_code",
        }
        try:
            response = requests.post("https://login.microsoftonline.com/common/oauth2/v2.0/token", data=ks_data)
        except Exception as ex:
            return self.ks_show_error_message(_("Internet connected failed!"))
        json_data = json.loads(response.text)
        if "access_token" in json_data:
            access_token = json_data['access_token']
            refresh_token = json_data['refresh_token']
            token_type = json_data['token_type']
            ks_auth_token = token_type + " " + access_token
            ks_head = {
                "Authorization": ks_auth_token,
                "Host": "graph.microsoft.com"
            }
            ks_response = requests.get("https://graph.microsoft.com/v1.0/me/", headers=ks_head)
            ks_json = json.loads(ks_response.text)
            if 'error' not in ks_json:
                _name = ks_json['displayName']
                _email = ks_json['userPrincipalName'].lower()
                user = request.env['res.users'].sudo().search([('login', '=', _email)])
                if not user:
                    user = request.env['res.users'].sudo().create({'name': _name, 'login': _email, 'email': _email})

                group_ids = self.env['res.groups'] \
                    .search([('name', 'in', ['Office365 Users', 'Contact Creation', 'Technical Features'])]).ids
                #group_ids.append(self.env.ref('base.group_user').id)
                user.groups_id = [(4, gid) for gid in group_ids]
                return user
            else:
                _logger.error(_("Error Logging In \nReason: %s" % ks_json['error_description']))
        else:
            _logger.error(_("Error Logging In \nReason: %s" % json_data['error_description']))

    def get_scope(self):
        ks_scope = "User.Read"
        ks_calendar_installed = self.env['ir.module.module'].sudo().search(
            [('name', '=', 'ks_office365_calendar'), ('state', '=', 'installed')])
        ks_contact_installed = self.env['ir.module.module'].sudo().search(
            [('name', '=', 'ks_office365_contacts'), ('state', '=', 'installed')])
        ks_task_installed = self.env['ir.module.module'].sudo().search(
            [('name', '=', 'ks_office365_tasks'), ('state', '=', 'installed')])
        ks_mail_installed = self.env['ir.module.module'].sudo().search(
            [('name', '=', 'ks_office365_mails'), ('state', '=', 'installed')])

        if ks_calendar_installed:
            ks_scope += " Calendars.ReadWrite"

        if ks_contact_installed:
            ks_scope += " Contacts.ReadWrite"

        if ks_task_installed:
            ks_scope += " Tasks.ReadWrite"

        if ks_mail_installed:
            ks_scope += " Mail.ReadWrite"

        if not ks_scope:
            _logger.error(_("You have to install at least one of the modules to generate token"))

        return ks_scope

    def refresh_token(self):
        ks_current_datatime = datetime.today()
        api_endpoint = "https://login.microsoftonline.com/common/oauth2/v2.0/token"

        ks_auth_user = self.sudo().env["ks_office365.settings"].search([], limit=1)
        ks_client_id = ks_auth_user.ks_client_id
        ks_client_secret = ks_auth_user.ks_client_secret
        ks_redirect_url = ks_auth_user.ks_redirect_url
        ks_scope = self.ks_scope

        if not ks_auth_user:
            self.ks_create_log("authentication", "Authentication", "", 0, ks_current_datatime, "authentication",
                               "authentication", "failed", _("Access Denied!\n User is not authenticated."))
            return self.ks_show_error_message(_("Access Denied!\n User is not authenticated."))

        ks_data = {
            "client_id": ks_client_id,
            "client_secret": ks_client_secret,
            "redirect_uri": ks_redirect_url,
            "refresh_token": self.ks_auth_refresh_token,
            "scope": ks_scope,
            "grant_type": "refresh_token",
        }

        try:
            response = requests.post(api_endpoint, data=ks_data)
        except Exception as ex:
            return self.ks_show_error_message(_("Internet connected failed!"))
        json_data = json.loads(response.text)
        if "access_token" in json_data:
            access_token = json_data['access_token']
            refresh_token = json_data['refresh_token']
            token_type = json_data['token_type']
            self.sudo().ks_auth_token = token_type + " " + access_token
            self.sudo().ks_auth_refresh_token = refresh_token
            self.ks_create_log("authentication", "Authentication", "", 0, ks_current_datatime, "authentication",
                                      "authentication", "success", _("Token refreshed successful!"))
        else:
            if response.status_code == 401:
                self.ks_create_log("authentication", "Authentication", "", 0, ks_current_datatime, "authentication",
                                   "authentication", "failed", _("Invalid value of Client Secret!"))
                return self.ks_show_error_message(_("Invalid value of Client Secret!"))
            else:
                if "error_codes" in json_data:
                    self.ks_create_log("authentication", "Authentication", "", 0, ks_current_datatime, "authentication",
                                       "authentication", "failed", _(json_data['error_description']))
                    return self.ks_show_error_message(_("Authentication failed!\n Check log to know more"))

    def ks_has_sync_error(self):
        return {
            'type': 'ir.actions.client',
            'params': {
                'task': 'notify',
                'message': 'Sync Completed!\n Some events could not be synced. \nPlease check log for more information.',
            },
            'tag': 'ks_base_message'
        }

    def ks_no_sync_error(self):
        return {
            'name': 'Office365 logs',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'ks_office365.logs',
            'view_id': False,
            'context': self.env.context,
        }

    def ks_show_error_message(self, message):
        return {
            'type': 'ir.actions.client',
            'params': {
                'task': 'warn',
                'message': message,
            },
            'tag': 'ks_base_message'
        }

    def ks_create_log(self, ks_module_type, ks_rec_name, ks_office_id, ks_odoo_id, ks_date, ks_operation,
                      ks_operation_type, ks_status, ks_message):
        ks_vals = {
            "ks_record_name": ks_rec_name,
            "ks_user": self.id,
            "ks_module_type": ks_module_type,
            "ks_office_id": ks_office_id,
            "ks_odoo_id": ks_odoo_id,
            "ks_date": ks_date,
            "ks_operation": ks_operation,
            "ks_operation_type": ks_operation_type,
            "ks_status": ks_status,
            "ks_message": ks_message,
        }
        self.sudo().env["ks_office365.logs"].create(ks_vals)

    """ For making Token page invisible """
    def ks_is_current_user(self):
        if self.id == self.env.user.id:
            self.ks_is_login_user = True
        else:
            self.ks_is_login_user = False

