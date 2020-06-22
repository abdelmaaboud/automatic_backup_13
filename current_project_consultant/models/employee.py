# -*- coding: utf-8 -*-
from odoo import fields, models


class Employee(models.Model):
    _inherit = 'hr.employee'

    timesheet_current_project_project_id = fields.Many2one('project.project', string="Current Working Project")
    timesheet_current_project_task_id = fields.Many2one('project.task', string="Current Working Task")

