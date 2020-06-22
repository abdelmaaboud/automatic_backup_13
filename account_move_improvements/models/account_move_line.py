# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    
    compute_taxes = fields.Boolean(string="Compute Taxes", default=False)
    
    @api.model
    def create(self, vals):
        if 'compute_taxes' in vals and vals['compute_taxes']:
            self = self.with_context(apply_taxes=True)
        return super(AccountMoveLine,self).create(vals)