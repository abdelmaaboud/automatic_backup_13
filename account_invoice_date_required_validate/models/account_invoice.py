# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_date_assign(self):
        for invoice in self:
            _logger.debug("\n\n DATE : %s", invoice.date_invoice)
            if invoice.date_invoice == False:
                raise UserError(_('No date specified on this invoice. Please set one manually. This module forbits the system to auto set a date on invoices.'))
        return super(AccountInvoice, self).action_date_assign()