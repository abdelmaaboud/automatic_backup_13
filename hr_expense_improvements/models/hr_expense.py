# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _


class HrExpense(models.Model):
    _inherit="hr.expense"
    
    @api.onchange('employee_id')
    def employee_id_onchange(self):
        self.analytic_account_id = self.employee_id.analytic_account_id.id
    