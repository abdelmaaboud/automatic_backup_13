# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
import logging
from datetime import datetime, timedelta
import pytz
import time
import math
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT,DEFAULT_SERVER_DATETIME_FORMAT
_logger = logging.getLogger(__name__)

class HrHolidays(models.Model):
    _inherit = 'hr.holidays'
    
    date_day_from = fields.Date(string="Date From")
    date_day_to = fields.Date(string="Date To")
    
    day_time_from = fields.Selection([
        ('morning', 'Morning'),
        ('midday', 'Midday')
    ], string="Day Time From", default='morning')
    day_time_to = fields.Selection([
        ('midday', 'Midday'),
        ('evening', 'Evening')
    ], string="Day Time From", default='evening')

    @api.multi
    def write(self, vals):
        for leave in self:
            date_from = leave.date_from
            date_to = leave.date_to
            
            # Compute and update the number of days
            if (date_to and date_from) and (date_from <= date_to):
                number_of_days_temp = 0
                number_of_days = 0
                number_of_days_temp = leave._get_number_of_days(date_from, date_to, leave.employee_id.id)
                if leave.type == 'remove':
                    number_of_days = -leave.number_of_days_temp
                else:
                    number_of_days = leave.number_of_days_temp
                vals.update({
                    'number_of_days_temp': number_of_days_temp,
                    'number_of_days': number_of_days,
                })
        return super(HrHolidays, self).write(vals)
    
    @api.constrains('date_from', 'date_to')
    def _check_date(self):
        for holiday in self:
            domain = [
                ('date_from', '<', holiday.date_to),
                ('date_to', '>', holiday.date_from),
                ('employee_id', '=', holiday.employee_id.id),
                ('id', '!=', holiday.id),
                ('type', '=', holiday.type),
                ('state', 'not in', ['cancel', 'refuse']),
            ]
            nholidays = self.search_count(domain)
            if nholidays:
                raise exceptions.ValidationError(_('You can not have 2 leaves that overlaps on same day!'))

#     @api.multi
#     @api.onchange('date_from', 'date_to')
#     def _changed_datetimes(self):
#         for leave in self:
#             if leave.date_from:
#                 leave.date_day_from = fields.Date.from_string(leave.date_from)
#                 leave.date_from = self.get_datetime_from_date_and_moment(fields.Date.from_string(leave.date_from), leave.day_time_from, leave.employee_id)
#             if leave.date_to:
#                 leave.date_day_to = fields.Date.from_string(leave.date_to)
#                 leave.date_to = self.get_datetime_from_date_and_moment(fields.Date.from_string(leave.date_to), leave.day_time_to, leave.employee_id)

    @api.multi
    @api.onchange('date_day_from', 'day_time_from', 'date_day_to', 'day_time_to')
    def _onchange_date_or_moment(self):
        for leave in self:
            if leave.employee_id and not leave.employee_id.resource_calendar_id:
                raise exceptions.Warning(_('The employee has no working hours'))

            if leave.date_day_from and leave.day_time_from:
                date_day_from = fields.Date.from_string(leave.date_day_from)
                leave.date_from = self.get_datetime_from_date_and_moment(date_day_from, leave.day_time_from, leave.employee_id)

            if leave.date_day_to and leave.day_time_to:
                date_day_to = fields.Date.from_string(leave.date_day_to)
                leave.date_to = self.get_datetime_from_date_and_moment(date_day_to, leave.day_time_to, leave.employee_id)

    # This method takes a date, a moment (morning/midday/evening) and an employee
    # It returns a datetime that represents the date+moment regarding the work calendar of the employee
    # e.g.: 1/04/2020 + midday for employee with standard 40h/week => will return 1/04/2020 13:00:00
    def get_datetime_from_date_and_moment(self, date, moment, employee_id):
        if not date or (not moment or moment == "") or not employee_id:
            return False

        # Get the hours from the moment of the day
        week_day = date.weekday()
        attendances = self.env['resource.calendar.attendance'].search([("calendar_id", '=', employee_id.resource_calendar_id.id), ('dayofweek', '=', week_day)])

        # Not during working time
        if len(attendances) == 0:
            if moment == "morning":
                return datetime(year=date.year, month=date.month, day=date.day, hour=8, minute=0, second=0)
            elif moment == "midday":
                return datetime(year=date.year, month=date.month, day=date.day, hour=12, minute=30, second=0)
            elif moment == "evening":
                return datetime(year=date.year, month=date.month, day=date.day, hour=18, minute=0, second=0)
        else:
            time = 0
            if moment == "morning":
                if len(attendances) == 1:
                    time = self.float_time_convert(attendances.hour_from).split(':')
                elif len(attendances) == 2:
                    time = self.float_time_convert(attendances[0].hour_from).split(':')
            elif moment == "midday":
                if len(attendances) == 1:
                    time = (self.float_time_convert((attendances.hour_from + attendances.hour_to) / 2).split(':'))
                elif len(attendances) == 2:
                    time = self.float_time_convert((attendances[0].hour_to + attendances[1].hour_from) / 2).split(':')
            elif moment == "evening":
                if len(attendances) == 1:
                    time = self.float_time_convert(attendances.hour_to).split(':')
                elif len(attendances) == 2:
                    time = self.float_time_convert(attendances[1].hour_to).split(':')

            return datetime(year=date.year, month=date.month, day=date.day, hour=int(time[0]) - 2, minute=int(time[1]), second=0)

    @api.model
    def float_time_convert(self, float_val):    
        factor = float_val < 0 and -1 or 1
        val = abs(float_val)
        hour = factor * int(math.floor(val))
        minute = int(round((val % 1) * 60))
        return format(hour, '02') + ':' + format(minute, '02')

