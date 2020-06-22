# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ProjectOnboarding(models.Model):
    _inherit = 'project.project'

    onboarding_project = fields.Boolean('Is an Onboarding Project', default=False)
    outboarding_project = fields.Boolean('Is an Outboarding Project', default=False)
    on_out_boarding_employee_id = fields.Many2one('hr.employee', 'Employee')
