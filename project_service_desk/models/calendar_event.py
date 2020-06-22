# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _

from datetime import datetime, timedelta

import logging
_logger = logging.getLogger(__name__)


class CalendarEventProject(models.Model):
    _inherit = ['calendar.event']

    def default_end_date(self):
        today = fields.Datetime.from_string(fields.Datetime.now())
        duration = timedelta(days=1)
        return today + duration

    planned_time = fields.Selection([('am', 'AM'), ('pm', 'PM'), ('am_pm', 'AM+PM'), ('specific', 'Specific time')], string='Planned on')

    project_id = fields.Many2one('project.project', string="Project")
    task_ids = fields.Many2many('project.task', string="Tasks", domain="[('project_id', '=', project_id)]")
    tasks_planned_hours = fields.Float(string="Planned time on tasks", compute='_compute_total_planned_hours')

    @api.multi
    @api.onchange('task_ids')
    def _compute_total_planned_hours(self):
        for forecast in self:
            forecast.tasks_planned_hours = 0
            for task in forecast.task_ids:
                forecast.tasks_planned_hours += task.planned_hours

    @api.multi
    @api.onchange('project_id')
    def compute_name(self):
        for event in self:
            if event.project_id:
                event.name = event.project_id.name

    """@api.multi
    @api.onchange('planned_time')
    def planned_time_changed(self):
        for forecast in self:
            # start_date
            start_date = datetime.strptime(forecast.start_date, DEFAULT_SERVER_DATETIME_FORMAT)

            # get today's line(s)
            lines = forecast.employee_id.resource_calendar_id.attendance_ids.filtered(lambda a: int(a.dayofweek) == int(start_date.weekday()))
            hour = start_date.hour + start_date.minute / 60.0
            for line in lines:
                if line.hour_from <= hour <= line.hour_to:
                    if forecast.planned_time == 'am':
                        forecast.start_date = start_date.replace(hour=int(line.hour_from) - 1)
                        forecast.end_date = start_date.replace(hour=int(line.hour_from + 3))
                    elif self.planned_time == 'pm':
                        forecast.start_date = start_date.replace(hour=int(line.hour_from + 4))
                        forecast.end_date = start_date.replace(hour=int(line.hour_to) - 1)
                    elif self.planned_time == 'am_pm':
                        forecast.start_date = start_date.replace(hour=int(line.hour_from) - 1)
                        forecast.end_date = start_date.replace(hour=int(line.hour_to) - 1)"""

    """@api.multi
    @api.onchange('start_date', 'end_date')
    @api.depends('start_date', 'end_date')
    def changed_dates(self):
        for forecast in self:
            forecast.resource_hours = float((datetime.strptime(forecast.end_date, DEFAULT_SERVER_DATETIME_FORMAT) - datetime.strptime(forecast.start_date, DEFAULT_SERVER_DATETIME_FORMAT)).seconds / 3600)
            """
