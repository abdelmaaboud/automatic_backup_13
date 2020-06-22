# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
import logging
_logger = logging.getLogger(__name__)

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'
    
    qty_processed_on_barcode_interface = fields.Float(string="Quantity Processed By Barcode Interface",default=0)