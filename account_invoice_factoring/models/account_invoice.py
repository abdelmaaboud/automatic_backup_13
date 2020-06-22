# -*- coding: utf-8 -*-

from odoo import models, fields, api

import logging
_logger = logging.getLogger(__name__)

class AccountInvoice(models.Model):
    _inherit = ['account.invoice']

    do_factoring = fields.Boolean(string="Do factoring", default=False)

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        self.do_factoring = self.partner_id.do_factoring

        return super(AccountInvoice, self)._onchange_partner_id()

    @api.model
    def create(self, values):
        if 'partner_id' in values:
            partner_id = self.env['res.partner'].search([('id', '=', values['partner_id'])])
            values.update({
                'do_factoring': partner_id.do_factoring,
            })
        return super(AccountInvoice, self).create(values)

