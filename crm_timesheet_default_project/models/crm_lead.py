# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
import logging
_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    def get_default_project(self):
        if self.team_id and self.team_id.timesheet_project_id:
            return self.team_id.timesheet_project_id
        elif 'default_team_id' in self.env.context:
            team_id = self.env['crm.team'].browse(self.env.context.get('default_team_id', 1))
            return team_id.timesheet_project_id
        return False

    project_id = fields.Many2one('project.project', default=get_default_project)