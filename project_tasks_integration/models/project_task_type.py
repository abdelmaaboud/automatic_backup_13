# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _

import logging
_logger = logging.getLogger(__name__)

class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'
    
    need_user_assignation = fields.Boolean(string="Need User Assignation")
    need_estimate = fields.Boolean()
