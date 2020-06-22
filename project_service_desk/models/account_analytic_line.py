# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class AccountAnalyticLineServiceDesk(models.Model):
    _inherit = ['account.analytic.line']

    unit_amount = fields.Float(default=0.25)
