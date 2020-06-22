# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
import logging
_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    partner_vat = fields.Char(string="Vendor's TIN", compute="_compute_partner_vat", store=True)

    @api.one
    @api.depends('partner_id')
    def _compute_partner_vat(self):
        self.partner_vat = self.partner_id.vat
