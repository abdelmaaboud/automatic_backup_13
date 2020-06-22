# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class HrProjectOnOutBoarding(models.Model):
    _name = 'hr.project.on.out.boarding'
    _description = 'Project On/Out Boarding Templates'

    name = fields.Char(required=True)
    type = fields.Selection([('onboarding', 'Onboarding'), ('outboarding', 'Outboarding')])
    project_id = fields.Many2one('project.project', 'Project template')
