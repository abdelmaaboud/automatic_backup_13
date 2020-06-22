# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
from odoo import api, models, fields

class HrHolidays(models.Model):
    _inherit = 'hr.holidays'

    company_id = fields.Many2one('res.company', "Company", compute='compute_company_id', store=True)
    
    @api.depends('employee_id')
    def compute_company_id(self):
        for hol in self:
            if hol.employee_id:
                hol.company_id = hol.employee_id.company_id.id
            else:
                hol.company_id = False
