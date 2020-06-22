# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    timesheet_project_id = fields.Many2one('project.project', string="Default Project for Timesheets")
