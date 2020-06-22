# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions

from odoo import models, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        result = super(SaleOrderLine, self).product_id_change()

        if self.product_id:
            vals = {}

            #get the product in partner lang
            partner = self.order_id.partner_id
            if partner.lang:
                product = self.product_id.with_context(lang=partner.lang)
            else:
                product = self.product_id

            name = ""
            if product.product_brand_id:
                name = product.product_brand_id.name + " - "

            #select the right description
            if product.description_sale:
                name = name + product.name + "\n" + product.description_sale
            elif product.description:
                name = name + product.name + "\n" + product.description
            else:
                name = name + product.name

            vals['name'] = name
            self.update(vals)

        return result


