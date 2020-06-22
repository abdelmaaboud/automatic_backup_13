from odoo import models, fields, api
import datetime
import calendar

import logging
_logger = logging.getLogger(__name__)

class ResUsersPlanning(models.Model):
    _inherit = ['res.users']
    
    receive_planning_by_mail = fields.Boolean(string="Receive Planning By Email", default=False, help="Receive every monday morning the user planning by email.")
    
    def cron_send_week_planning_email(self):
        _logger.debug("Week planning email")
        
        user_ids = self.env['res.users'].search([("share", '=', False), ('receive_planning_by_mail', '=', True)])
        
        my_date = datetime.date.today()
            
        start = my_date - datetime.timedelta(days=my_date.weekday())
        end = start + datetime.timedelta(days=6)
        
        dd = [start + datetime.timedelta(days=x) for x in range((end-start).days + 1)]
        
        for user_id in user_ids:
            event_by_days =[]
            for d in dd:
                start_day = datetime.datetime(d.year, d.month, d.day)
                end_day = start_day + datetime.timedelta(1)
                calendar_event_ids = self.env['calendar.event'].search([('partner_ids', 'in', [user_id.partner_id.id]), 
                                                                    ('start_datetime', '>=', fields.Date.to_string(start_day)),
                                                                ('start_datetime', '<', fields.Date.to_string(end_day))], order='start_datetime asc')
                if calendar_event_ids:
                    event_by_days.append({
                            d.strftime('%A - %d %b %Y'): calendar_event_ids
                        })

                    
            if event_by_days:
                data = {
                    'partner_id': user_id.partner_id,
                    'event_by_days': event_by_days,
                }
                id = self.env.ref("user_planning_reminder.week_planning").id
                self.env['mail.template'].browse(id).with_context(data).send_mail(self.id, force_send=True, email_values=None)

