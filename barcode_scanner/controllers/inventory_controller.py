# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import Response
import logging
import json
from datetime import date
_logger = logging.getLogger(__name__)

class InventoryController(http.Controller):
    @http.route('/barcode_scanner/post/inventory/', auth="public", methods=['POST'], website=True, type="json")
    def createInventory(self, location_key, product_ids_and_quant, token, **kw):
        if not http.request.env["res.users"].sudo().check_if_token_has_barcode_interface_access(token):
            return {
                'error':{
                    'message': 'Connection expired, try to login again.',
                    'logout': True
                }
            }
        product_ids = []
        for product_id_and_quant in product_ids_and_quant:
            _logger.debug(product_id_and_quant)
            product_ids.append(product_id_and_quant['id'])
            
        
        location_id = http.request.env["stock.location"].search([('id', '=', location_key)])
        inventory = http.request.env['stock.inventory'].sudo().create({
            'name': location_id.name + " (" + str(date.today()) + ")",
            'location_id': location_key,
            'product_ids': product_ids
        })
        for product_id_and_quant in product_ids_and_quant:   
            inventory_line = http.request.env['stock.inventory.line'].sudo().create({
                'inventory_id': inventory.id,
                'location_id': inventory.location_id.id,
                'product_id': product_id_and_quant["id"],
                'product_qty': product_id_and_quant["qty"]
            })

        inventory.action_done()

        if inventory.state == 'done':
            return {
                'result':{
                    
                }
            }
        else:
            return {'error': {'message': 'Something went wrong'}}
