# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
import logging
from odoo import models, fields, api, _
import datetime

_logger = logging.getLogger(__name__)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.model
    def create(self, vals):
        res = super(PurchaseOrderLine, self).create(vals)
        if res.sale_line_id and res.sale_line_id.order_id.carrier_id and res.sale_line_id.order_id.carrier_id.product_po_id:
            if  res.sale_line_id.order_id.carrier_id.product_po_id.id not in res.order_id.order_line.mapped('product_id').ids:
                r = self.env['purchase.order.line'].create({
                    'product_id': res.sale_line_id.order_id.carrier_id.product_po_id.id,
                    'product_qty': 1,
                    'product_uom': res.sale_line_id.order_id.carrier_id.product_po_id.uom_po_id.id,
                    'price_unit': 0.0,
                    'name': res.sale_line_id.order_id.carrier_id.product_po_id.name,
                    'sale_line_id': res.sale_line_id.id,
                    'order_id': res.order_id.id,
                    'date_planned': datetime.datetime.now()
                })
                r.onchange_product_id()
        return res

    # @api.multi
    # def write(self, vals):
    #     result = super(PurchaseOrderLine, self).write(vals)
    #     for res in self:
    #         if res.sale_line_id and res.sale_line_id.order_id.carrier_id and res.sale_line_id.order_id.carrier_id.product_po_id:
    #             if res.order_id.order_line.mapped(
    #                     'product_id.id') not in res.sale_line_id.order_id.carrier_id.product_po_id.id:
    #                 r = self.env['purchase.order.line'].create({
    #                     'product_id': res.sale_line_id.order_id.carrier_id.product_po_id.id,
    #                     'product_qty': 1,
    #                     'order_id': res.order_id.id,
    #                 })
    #                 r.onchange_product_id()

