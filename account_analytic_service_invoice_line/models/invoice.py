# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class AccountInvoiceLine(models.Model):
    _inherit = ['account.invoice.line']

    @api.model
    def create(self, values):
        product = self.env['product.product'].search([
            ('id', '=', values['product_id'])]) if values.get('product_id') else self.product_id

        config_error = False

        if product and product.type != 'service':
            if product.income_analytic_account_id:
                values['account_analytic_id'] = product.income_analytic_account_id.id
            elif product.categ_id and product.categ_id and product.categ_id.income_analytic_account_id:
                values['account_analytic_id'] = product.categ_id.income_analytic_account_id.id
            else:
                config_error = True

        record = super(AccountInvoiceLine, self).create(values)

        if config_error:
            record.account_analytic_id = False

        return record
