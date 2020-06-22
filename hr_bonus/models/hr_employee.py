# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
import logging
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


class Employee(models.Model):
    _inherit = 'hr.employee'

    bonus_count = fields.Integer(compute='_compute_bonus_count')

    @api.one
    def _compute_bonus_count(self):
        self.bonus_count = len(self.env['hr.bonus'].search([('employee_id.id', '=', self.id)]))
