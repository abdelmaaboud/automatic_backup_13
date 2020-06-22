# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    equipment_ids = fields.One2many('maintenance.equipment', 'employee_id', 'Equipments')
    equipment_count = fields.Integer(compute='_compute_equipment_count', string='Number of equipments')

    @api.one
    @api.depends('equipment_ids')
    def _compute_equipment_count(self):
        self.equipment_count = len(self.equipment_ids)
        return len(self.equipment_ids)
