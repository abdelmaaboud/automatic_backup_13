# -*- coding: utf-8 -*-

import datetime
from datetime import datetime
from odoo import SUPERUSER_ID
from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)

class DeadLineReminder(models.Model):
    _inherit = "project.task"
    
    date_reminder = fields.Date(string="Remind by mail at : ")
    
    @api.model
    def _cron_deadline_reminder(self):
        for task in self.env['project.task'].search([('date_reminder', '!=', None),
                                                     ('task_reminder', '=', True), ('user_id', '!=', None)]):
            reminder_date = datetime.strptime(task.date_reminder, '%Y-%m-%d').date()
            today = datetime.now().date()
            if reminder_date == today and task:
                template_id = self.env['ir.model.data'].get_object_reference(
                                                      'task_deadline_reminder',
                                                      'email_template_edi_deadline_reminder')[1]
                if template_id:
                    email_template_obj = self.env['mail.template'].browse(template_id)
                    values = email_template_obj.generate_email(task.id, fields=None)
                    values['email_to'] = task.user_id.email
                    values['res_id'] = False
                    mail_mail_obj = self.env['mail.mail']
                    msg_id = mail_mail_obj.create(values)
                    if msg_id:
                        msg_id.send()
        return True