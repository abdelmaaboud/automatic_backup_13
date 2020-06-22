# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
import logging
from odoo import models, fields, api, _


_logger = logging.getLogger(__name__)


class SaleOrderExpirationConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sale_order_cancel_delay = fields.Integer(string="Cancellation delay after expiration", required=True, default=14)
