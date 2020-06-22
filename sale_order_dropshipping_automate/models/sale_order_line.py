# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class SaleOrderLineDropshippingAutomate(models.Model):
    _inherit = 'sale.order.line'

    route_id = fields.Many2one(default=lambda self: self.get_route_from_order())

    def get_route_from_order(self):
        context = dict(self.env.context)
        if 'default_carrier_id' in context:
            carrier = self.env['delivery.carrier'].browse(context['default_carrier_id'])
            if carrier and carrier.route_id:
                return carrier.route_id.id
        return False
