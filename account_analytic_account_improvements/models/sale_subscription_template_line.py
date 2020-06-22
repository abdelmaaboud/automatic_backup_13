# -*- coding: utf-8 -*-

from odoo import models, fields, api

import datetime
import logging
_logger = logging.getLogger(__name__)


class SaleSubscriptionTemplateLine(models.Model):
    _name = 'sale.subscription.template.line'

    template_id = fields.Many2one('sale.subscription.template', string="Template")
    product_id = fields.Many2one('product.product', string="Product", required=True)
    name = fields.Char(string="Description", required=True)
    quantity = fields.Float(string="Quantity", default=1.0)
    uom_id = fields.Many2one('product.uom', string='Unit of Measure', required=True)
    price_unit = fields.Float(string="Unit Price")
    discount = fields.Float(string="Discount (%)")
    price_subtotal = fields.Float(string="Sub Total")

    @api.onchange('product_id', 'price_unit', 'quantity', 'discount')
    def product_change(self):
        for line in self:
            # Name
            line.name = line.product_id.display_name
            if line.product_id.description_sale:
                line.name += '\n' + line.product_id.description_sale

            # UoM
            if not line.uom_id:
                line.uom_id = line.product_id.uom_id.id

            # Price
            line.price_unit = line.product_id.lst_price

            # Subtotal
            line.price_subtotal = line.quantity * line.price_unit * (100.0 - line.discount) / 100.0

