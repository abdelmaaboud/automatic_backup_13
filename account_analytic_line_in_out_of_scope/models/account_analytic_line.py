# -*- coding: utf-8 -*-
from odoo import models, fields

import logging
_logger = logging.getLogger(__name__)


class AccountAnalyticLineInOutOfScope(models.Model):
    _inherit = ['account.analytic.line']

    out_of_scope = fields.Boolean(string="Out of Scope", help="Check this box if the work is out of scope of the project", default=False)
