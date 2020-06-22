# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    
    # This method is a copy of the base method used to compute the timesheet stats info
    @api.multi
    @api.depends('analytic_account_id.line_ids')
    def _compute_timesheet_ids(self):
        for order in self:
            if order.analytic_account_id:
                order.timesheet_ids = self.env['account.analytic.line'].search(
                    [('so_line', 'in', order.order_line.ids),
                        ('amount', '<=', 0.0),
                        ('project_id', '!=', False)])
            else:
                order.timesheet_ids = []
            # From here, it's different.
            # We now make the sum of all unit_amount of timesheet_ids of the S.O.
            hours_sum = 0
            for timesheet_id in order.timesheet_ids:
                hours_sum = hours_sum + timesheet_id.unit_amount
            order.timesheet_count = hours_sum