# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _

import logging
_logger = logging.getLogger(__name__)
    
    
class SaleOrderConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    sale_order_cancel_delay = fields.Integer(string="Cancellation delay after expiration", required=True, default=14)
