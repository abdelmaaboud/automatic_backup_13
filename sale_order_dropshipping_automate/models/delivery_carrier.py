# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class DeliveryCarrierAutomate(models.Model):
    _inherit = 'delivery.carrier'

    route_id = fields.Many2one('stock.location.route', 'Route used')
