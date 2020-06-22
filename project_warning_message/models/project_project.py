# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _

class ProjectProject(models.Model):
    _inherit = ['project.project']

    warning_text = fields.Text(string="Warning Text", help="The content of this field will be displayed on every Task and Timesheet of this project")
