# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = ['sale.order.line']

    margin = fields.Float(compute='_compute_margin_for_line', store=True)

    @api.multi
    @api.depends('product_id', 'product_uom_qty', 'price_unit', 'discount')
    def _compute_margin_for_line(self):
        for sol in self:
            product_cost_price = sol.product_id.product_tmpl_id.standard_price \
                if sol.product_id.product_tmpl_id else sol.product_id.standard_price
            if product_cost_price <= 0:
                sol.margin = -1
            else:
                sol.margin = (sol.price_unit * (1 - (sol.discount / 100))) - product_cost_price


class SaleOrder(models.Model):
    _inherit = ['sale.order']

    total_margin = fields.Float(compute='_compute_margins', store=True)

    @api.multi
    @api.onchange('order_line')
    @api.depends('order_line')
    def _compute_margins(self):
        for my_so in self:
            margin = 0
            if my_so.order_line:
                for sale_order_line in my_so.order_line:
                    sale_order_line._compute_margin_for_line()
                    line_margin = sale_order_line.margin * sale_order_line.product_uom_qty
                    margin += line_margin

            my_so.total_margin = margin
