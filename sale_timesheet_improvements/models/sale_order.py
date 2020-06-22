from odoo import models, fields, api, _, exceptions

import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_create_invoice(self):
        p = self.partner_id
        if p.invoice_warn == 'no-message' and p.parent_id:
            p = p.parent_id
        if p.invoice_warn != 'no-message':
            # Block if partner only has warning but parent company is blocked
            if p.invoice_warn != 'block' and p.parent_id and p.parent_id.invoice_warn == 'block':
                p = p.parent_id
            if p.invoice_warn == 'block':
                raise exceptions.Warning(p.invoice_warn_msg)

        action = self.env.ref('sale.action_view_sale_advance_payment_inv').read()[0]
        action['context'] = {'default_invoice_warn_msg': p.invoice_warn_msg}
        return action

    @api.multi
    def create_invoices(self):
        res = super(SaleOrder, self).create_invoices()
        
        timesheet_ids = self.env['account.analytic.line'].search(
                    [('so_line', 'in', self.order_line.ids),
                        ('amount', '<=', 0.0),
                        ('project_id', '!=', False), ('validated', '=', False)])
        for timesheet_id in timesheet_ids:
            timesheet_id.timesheet_invoice_id = False
            
        return res
        