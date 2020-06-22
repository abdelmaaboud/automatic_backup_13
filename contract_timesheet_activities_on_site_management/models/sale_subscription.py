# -*- coding: utf-8 -*-

from odoo import models, fields, api

import datetime
import logging
_logger = logging.getLogger(__name__)


class SaleSubscription(models.Model):
    _inherit = ['sale.subscription']
    
    on_site_product = fields.Many2one('product.product', string="Travel Product", help="Product that will be used to compute the price of the travel when the work is done on site.")
    on_site_invoice_by_km = fields.Boolean(string="Invoice by km", help="True: price = km * on site product public price, False: price = on site product public price")
    on_site_distance_in_km = fields.Float("Distance in km")
