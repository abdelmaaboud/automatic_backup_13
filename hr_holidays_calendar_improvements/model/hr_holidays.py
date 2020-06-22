# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HrHolidays(models.Model):
    _inherit = 'hr.holidays'
    
    state_info = fields.Char(compute='_compute_state_info', store=False)
    
    @api.depends('state')
    @api.one
    def _compute_state_info(self):
        states_dict = {
            'draft': 'To Submit',
            'cancel': 'Cancelled',
            'confirm': 'To Approve',
            'refuse': 'Refused',
            'validate1': 'Second Approval',
            'validate': 'Approved',
        }
        self.state_info = states_dict[self.state]
