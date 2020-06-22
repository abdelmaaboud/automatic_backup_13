# -*- coding: utf-8 -*-
# (c) 2018 - AbAKUS IT SOLUTIONS

import logging
from pprint import pformat
from odoo import models, api, fields, _
_logger = logging.getLogger(__name__)


class AccountAccount(models.Model):
    _inherit = 'account.account'

    is_analytic_mandatory = fields.Boolean(string="Require Analytic")
