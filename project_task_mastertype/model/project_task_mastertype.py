# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
import logging
_logger = logging.getLogger(__name__)

class ProjectTaskMasterType(models.Model):
    _name = 'project.task.mastertype'

    name = fields.Char(string="Name", translate=True)
    code = fields.Char(string="Code", translate=True)
    sequence = fields.Integer(string="Sequence")
    active = fields.Boolean(string="Active", default=True)
