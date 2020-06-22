# -*- coding: utf-8 -*-
from odoo import models, fields
import datetime
from datetime import date
import logging

_logger = logging.getLogger(__name__)

def calculate_age(born):
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def string_to_date(date_string, format_string):
    return datetime.datetime.strptime(date_string, format_string).date()


def string_to_datetime(date_string, format_string):
    return datetime.datetime.strptime(date_string, format_string)


class hr_employee_date_reminder(models.Model):
    _inherit = 'hr.employee'

    def send_email_on_birthday_or_entry_date(self):
        today = datetime.datetime.now()
        today_month_day = '%-' + today.strftime('%m') + '-' + today.strftime('%d')

        employee_obj = self.env['hr.employee']
        employee_birthday_id = employee_obj.search([('birthday', 'like', today_month_day)])
        employee_startday_id = employee_obj.search([('entry_date', 'like', today_month_day)])

        employee_string = ""
        content = ""
        notify = False

        if employee_birthday_id:
            for val in employee_birthday_id:
                age = calculate_age(string_to_date(val.birthday, "%Y-%m-%d"))
                employee_string = '%s%s (%s years). ' % (employee_string, val.name, str(age))
            content = 'Birthday on %s/%s/%s : %s<br/>' % (today.strftime('%d'), today.strftime('%m'), today.strftime('%Y'), employee_string)
            notify = True

        if employee_startday_id:
            employee_string = ""
            for val in employee_startday_id:
                entrydate = string_to_date(val.entry_date, "%Y-%m-%d")
                entrydatetime = string_to_datetime(val.entry_date, "%Y-%m-%d")
                age = calculate_age(entrydate)
                employee_string = '%s%s (%s/%s/%s, since %s years). ' % (employee_string, val.name, entrydatetime.strftime('%d'), entrydatetime.strftime('%m'), entrydatetime.strftime('%Y'), str(age))
            content = '%s/<br />Congratulate: %s/ at AbAKUS<br/>' % (content, employee_string)
            notify = True

        if notify:
            user_manager_ids = employee_obj.search([('manager', '=', True)])
            if user_manager_ids:
                for val in user_manager_ids:
                    mail_mail = self.env['mail.mail']
                    mail_id = mail_mail.create({
                        'body_html': content,
                        'subject': 'Odoo birthday and entry date reminder',
                        'email_to': val.work_email,
                        'email_from': "odoo@abakusitsolutions.eu",
                        'state': 'outgoing',
                        'message_type': 'email',
                        'auto_delete': True,
                    })
                    mail_id.send()
        return None
