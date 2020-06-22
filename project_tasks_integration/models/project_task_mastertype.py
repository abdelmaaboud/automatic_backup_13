# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _

import logging
_logger = logging.getLogger(__name__)

class ProjectTaskMasterType(models.Model):
    _inherit = 'project.task.mastertype'

    need_estimate = fields.Boolean()