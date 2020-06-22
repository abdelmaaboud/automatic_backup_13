# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class StockInventory(models.Model):
    _inherit = ['stock.inventory']

    total_value = fields.Float(compute='_compute_value')

    @api.multi
    @api.onchange('order_line')
    def _compute_value(self):
        for sto in self:
            value = 0
            for line in sto.line_ids:
                value += round(float(line.value), 2)

            sto.total_value = round(float(value), 2)


class StockInventoryLine(models.Model):
    _inherit = ['stock.inventory.line']

    # New field
    value = fields.Float(compute='_compute_value_for_line')

    @api.multi
    def _compute_value_for_line(self):
        for sto in self:
            if len(sto.product_id.seller_ids) < 1:  # Product has no sellers
                sto.value = round(float(sto.product_id.standard_price * sto.product_qty), 2)

            else:  # has sellers
                suppliers = sto.product_id.seller_ids.sorted(key=lambda r: r.sequence)
                right_supplier = suppliers[0]
                sto.value = round(float(right_supplier.price * sto.product_qty), 2)
