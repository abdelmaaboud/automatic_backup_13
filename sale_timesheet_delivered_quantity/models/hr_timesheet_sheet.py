from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class HrTimesheetSheet(models.Model):
    _inherit = ['hr_timesheet.sheet']

    @api.multi
    def write(self, vals):
        ret = super(HrTimesheetSheet, self).write(vals)

        if ('state' in vals) and (vals['state'] != 'done'):
            for line in self.timesheet_ids:
                line.validated = False

        if ('state' in vals) and (vals['state'] == 'done'):
            for line in self.timesheet_ids:
                line.validated = True # Mark line as validated
                order_id = self.env['sale.order'].search([('analytic_account_id', '=', line.account_id.id)])
                order_id.order_line.sudo()._analytic_compute_delivered_quantity()
        return ret
