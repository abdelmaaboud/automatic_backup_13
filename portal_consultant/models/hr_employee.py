# -*- coding: utf-8 -*-
from odoo import fields, models, api
import logging

_logger = logging.getLogger(__name__)

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    is_consultant = fields.Boolean(string="Consultant", related='user_id.is_consultant')

    @api.multi
    def change_consultant_rights(self):
        self.user_id.change_consultant_rights()
