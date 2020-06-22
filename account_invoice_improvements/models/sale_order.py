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
                _logger.debug("\n\nTEST")
                raise exceptions.Warning(p.invoice_warn_msg)

        action = self.env.ref('sale.action_view_sale_advance_payment_inv').read()[0]
        action['context'] = {'default_invoice_warn_msg': p.invoice_warn_msg}
        return action
