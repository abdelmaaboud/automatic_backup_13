from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)

class AccountInvoiceImproved(models.Model):
    _inherit = 'account.invoice'
    
    def _get_compute_timesheet_revenue_domain(self, so_line_ids):
        return [
            ('so_line', 'in', so_line_ids),
            ('project_id', '!=', False),
            ('timesheet_invoice_id', '=', False),
            ('timesheet_invoice_type', 'in', ['billable_time', 'billable_fixed']),
            ('sheet_id.state', '=', 'done')
        ]
    
    @api.multi
    def action_cancel(self):
        res = super(AccountInvoiceImproved, self).action_cancel()
        if self.timesheet_ids:
            for timesheet_id in self.timesheet_ids:
                timesheet_id.write({
                    'timesheet_invoice_id': False
                })
        return res