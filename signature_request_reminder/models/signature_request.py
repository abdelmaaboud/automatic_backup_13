from odoo import api, fields, models, _
import datetime
from datetime import timedelta
import calendar
from werkzeug.urls import url_join

import logging

_logger = logging.getLogger(__name__)

class SignatureRequest(models.Model):
    _inherit='signature.request'
    
    send_reminder = fields.Boolean(string="Send Reminder", default=True)
    last_sent_reminder = fields.Datetime(string="Last Sent Reminder")
    day_before_send_reminder = fields.Integer(string="Number of days between reminder", default=2)
    first_send_date = fields.Datetime(string="First Send Date")
    
    @api.multi
    def action_sent(self, subject=None, message=None):
        res = super(SignatureRequest, self).action_sent(subject, message)
        if not self.first_send_date:
            self.write({'first_send_date': fields.Datetime.now()})
        return res
        
    
    def cron_send_reminder_email(self):
        signature_request_ids = self.env['signature.request'].search([('send_reminder', '=', True), ('state', '=', 'sent'), ('first_send_date', '!=', False)])
        now = fields.Datetime.now()
        
        for signature_request_id in signature_request_ids:
            # base_url = self.env['ir.config_parameter'].get_param('web.base.url')
            # link = url_join(base_url, "sign/document/%(request_id)s/%(access_token)s" % {'request_id': signature_request_id.id, 'access_token': signature_request_id.access_token})
        
            # template_id = self.env.ref("signature_request_reminder.signature_request_reminder_mail_template").id
            # self.env['mail.template'].browse(template_id).with_context(link=link).send_mail(signature_request_id.id, force_send=True)
            datetime_format = '%Y-%m-%d %H:%M:%S.%f'
            diff = fields.Datetime.from_string(now) - fields.Datetime.from_string(signature_request_id.first_send_date)

            if diff.days >= signature_request_id.day_before_send_reminder:
                signature_request_id.send_follower_accesses(followers = signature_request_id.message_partner_ids)
                signature_request_id.send_signature_accesses()
                signature_request_id.write({'last_sent_reminder': fields.Datetime.now() })