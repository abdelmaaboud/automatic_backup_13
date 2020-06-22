# -*- coding: utf-8 -*-

from odoo import models, fields, api

import logging
_logger = logging.getLogger(__name__)

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.one
    def _prepare_analytic_line(self):
        res = super(AccountMoveLine, self)._prepare_analytic_line()
        res = res[0] # Don't know why we need to to get the first element (dict) of res (which is a list) but it's like that
        if 'invoice_id' not in res:
            #For customer invoice, link analytic line to the invoice so it is not proposed for invoicing in Bill Tasks Work
            invoice_id = self.invoice_id and self.invoice_id.type in ('out_invoice', 'out_refund') and self.invoice_id or False
            # Only if 'invoice_id' exists because lines could be created outside an invoice system, for instance in expenses
            if invoice_id:
                res.update({
                    'invoice_id': invoice_id.id,
                })
        return res
