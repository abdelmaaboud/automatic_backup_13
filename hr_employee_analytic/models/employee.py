# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
from odoo import models, fields
import logging
_logger = logging.getLogger(__name__)


class EmployeeAnalytic(models.Model):
    _inherit = 'hr.employee'

    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account")
