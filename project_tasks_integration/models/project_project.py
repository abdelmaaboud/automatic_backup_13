# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)

class Project(models.Model):
    _inherit = ['project.project']

    accept_email_from_support = fields.Boolean(string="Match emails from support on this project", default=True)
