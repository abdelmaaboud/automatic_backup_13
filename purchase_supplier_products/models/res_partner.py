# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _

import logging
_logger = logging.getLogger(__name__)
    
    
class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    vendor_products_count = fields.Integer(string="Vendor Products Count", compute='_compute_vendor_products_count')
    
    @api.one
    def _compute_vendor_products_count(self):
        self.vendor_products_count = self.env['product.product'].search_count([('seller_ids.name', '=', self.id)])