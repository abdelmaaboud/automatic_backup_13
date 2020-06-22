# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions

from odoo import models, api


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.onchange('product_id')
    def _onchange_product_id(self):
        result = super(AccountInvoiceLine, self)._onchange_product_id()

        if self.product_id:
            vals = {}

            #get the product in partner lang
            partner = self.invoice_id.partner_id
            if partner.lang:
                product = self.product_id.with_context(lang=partner.lang)
            else:
                product = self.product_id

            #select the good description
            if self.invoice_id.type in ('in_invoice', 'in_refund'):
                if product.description_purchase:
                    vals['name'] = product.description_purchase
            else:
                if product.description_sale:
                    vals['name'] = product.description_sale

            #if not description_purchase or description_sale in product
            if 'name' not in vals:
                if self.product_id.description:
                    vals['name'] = self.product_id.description
                else:
                    vals['name'] = self.product_id.name

            self.update(vals)

        return result

