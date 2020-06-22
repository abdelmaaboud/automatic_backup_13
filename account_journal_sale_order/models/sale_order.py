# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    journal_id = fields.Many2one('account.journal', string="Accounting Journal", required=True, default=lambda self: self._get_default_journal())

    def _get_default_journal(self):
        journal = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        journal_id = self.env['account.journal'].search([('id', '=', journal)])
        return journal_id

    @api.multi
    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        if self.journal_id.id != invoice_vals['journal_id']:
            invoice_vals['journal_id'] = self.journal_id.id
        return invoice_vals
