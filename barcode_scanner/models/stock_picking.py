# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
import logging
_logger = logging.getLogger(__name__)

class Picking(models.Model):
    _inherit = "stock.picking"
    
    @api.multi
    def action_done(self):
        res = super(Picking, self).action_done()
        for move_line in self.move_line_ids:
            if move_line.qty_processed_on_barcode_interface > 0:
                quant = self.env["stock.quant"].search([('product_id', '=', move_line.product_id.id),('location_id', '=', move_line.location_dest_id.id) ], limit=1)
                quant._update_available_quantity(move_line.product_id, move_line.location_dest_id, float(move_line.qty_processed_on_barcode_interface) * -1)
                move_line.qty_processed_on_barcode_interface = 0
        return res