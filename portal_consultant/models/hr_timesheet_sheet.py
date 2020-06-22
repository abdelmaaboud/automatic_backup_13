# -*- coding: utf-8 -*-
import logging
from datetime import timedelta
from odoo import fields, models, api
from odoo.http import request

_logger = logging.getLogger(__name__)


class hr_timesheet_sheet_delta_dates(models.Model):
    _inherit = 'hr_timesheet.sheet'

    # custom_name = fields.Char()
    timesheet_project_2 = fields.Many2one('project.project', string="Second project ID")
    timesheet_task_2 = fields.Many2one('project.task', string="Second task ID")

    def dates_between_str_dates(self, date1, date2, mode='date'):
        def is_day_off(date):
            for day_off in self.employee_id.resource_calendar_id.global_leave_ids:
                if date >= fields.Date.from_string(day_off.date_from) and date <= fields.Date.from_string(day_off.date_to):
                    return True
            return False
            
            
        date_from = fields.Date.from_string(date1)
        date_to = fields.Date.from_string(date2)

        delta = date_to - date_from

        if delta.days < 0 or not mode:
            return []

        res = []
        
        daysofweek = []
        for attendance in self.employee_id.resource_calendar_id.attendance_ids:
            daysofweek.append(attendance.dayofweek)
        
        for n in range(delta.days + 1):
            if mode == 'date':
                date_to_append = date_from + timedelta(days=n)
                if str(date_to_append.weekday()) in daysofweek and not is_day_off(date_to_append):
                    res.append(date_to_append)
            if mode == 'count':
                return delta.days + 1
            
        return res

    def get_unit_amount_for_employee_by_day_and_aal(self, employee_id, task_date, task):
        if task:
            lines = request.env['account.analytic.line'].sudo().search(
                [("employee_id", '=', employee_id), ("date", '=', task_date), ("task_id", '=', task.id)])
            total_time_spent = 0
            for line in lines:
                total_time_spent += line.unit_amount
            if total_time_spent != 0:
                return total_time_spent
        return 0

    def get_unit_amount_for_employee_by_day_and_aal1_and_aal2(self, employee_id, aal_date, aal_1, aal_2):
        lines = request.env['account.analytic.line'].sudo().search(
            [("employee_id", '=', employee_id), ("date", '=', aal_date), ("account_id", '=', aal_1)])
        total_time_spent = 0
        for line in lines:
            total_time_spent += line.unit_amount
        lines = request.env['account.analytic.line'].sudo().search(
            [("employee_id", '=', employee_id), ("date", '=', aal_date), ("account_id", '=', aal_2)])
        for line in lines:
            total_time_spent += line.unit_amount
        if total_time_spent != 0:
            return self.conv_float_time(total_time_spent)
        else:
            return 0

    def conv_float_time(self, value):
        hours, minutes = divmod(value * 60, 60)
        return '%02d:%02d' % (hours, minutes)

