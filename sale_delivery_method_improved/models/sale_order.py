# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    delivery_costs_applied = fields.Boolean()

    @api.multi
    def action_confirm(self):
        """" Only set the 'invoice_shipping_on_delivery' field to False because we don't want any line to be created
         automatically. But set the 'delivery_costs_applied' field to True if the delivery line has a price so will
         be invoiced """
        res = super(SaleOrder, self).action_confirm()
        for sale_order in self:
            sale_order.invoice_shipping_on_delivery = False
            sale_order.delivery_costs_applied = \
                any([(line.is_delivery and line.price_unit > 0) for line in sale_order.order_line])
        return res

    @api.multi
    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals['carrier_id'] = self.carrier_id.id if self.delivery_costs_applied else False
        return invoice_vals
