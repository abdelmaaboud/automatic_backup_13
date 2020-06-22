from odoo import models, fields, api


class OfficeSettings(models.Model):
    _name = "ks_office365.settings"
    _rec_name = "rec_name"
    _description = "Store azure credentials and authentication module"

    rec_name = fields.Char("Settings", default="Office365 Authentication")
    ks_user = fields.Many2one("res.users", default=lambda self: self.env.user.id)

    ks_client_id = fields.Char("Client ID")
    ks_client_secret = fields.Char("Client Secret")
    ks_redirect_url = fields.Char("Redirect URL")
    ks_scope = fields.Char("Scope", default="")

    ks_office_login = fields.Boolean(default=False)
    ks_office_login_code = fields.Char(default=False)

    ks_sync_individual = fields.Boolean("Sync Individual Calendar Event", default=False,
                                        help="This will allow you to sync an event automatically when it is created or "
                                             "attendee is updated in odoo calendar and will send instant email "
                                             "notification to the attendees of the event.")
    ks_dont_sync = fields.Boolean(default=False)

    @api.model
    def ks_get_code_url(self):
        ks_admin = self.sudo().env['ks_office365.settings'].search([], limit=1)
        ks_client_id = ks_admin.ks_client_id
        ks_redirect_url = ks_admin.ks_redirect_url
        ks_response_type = "code"
        ks_response_mode = "query"
        ks_state = "office_login"
        ks_scope = "offline_access User.Read"

        data = (ks_client_id, ks_response_type, ks_redirect_url, ks_scope, ks_response_mode, ks_state)
        url = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id=%s" \
              "&response_type=%s&redirect_uri=%s&scope=%s&response_mode=%s&state=%s" % data
        return url
