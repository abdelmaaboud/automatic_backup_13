# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class SaleOrderDropshippingAutomate(models.Model):
    _inherit = 'sale.order'

    @api.multi
    @api.onchange('carrier_id')
    def change_route_on_lines(self):
        for my_so in self:
            for line in my_so.order_line:
                line.route_id = my_so.carrier_id.route_id
