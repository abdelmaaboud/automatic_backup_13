# -*- coding: utf-8 -*-

from odoo import models, fields, api

import datetime
import logging
_logger = logging.getLogger(__name__)

class AnalyticLine(models.Model):
    _inherit = ['account.analytic.line']

    on_site = fields.Boolean(string="On site", help="Check this box if the work has not been done at Service Desk but On Site (by the Customer)", default=False)
