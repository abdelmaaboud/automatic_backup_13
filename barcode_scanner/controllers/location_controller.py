# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import Response
import logging
import json
_logger = logging.getLogger(__name__)

class LocationController(http.Controller):
    @http.route('/barcode_scanner/get/location', auth="public", methods=['POST'], website=True, type="json")
    def get_location(self, location_key, token, **kw):
        if not http.request.env["res.users"].sudo().check_if_token_has_barcode_interface_access(token):
            return {
                'error':{
                    'message': 'Connection expired, try to login again.',
                    'logout': True
                }
            }
        location = http.request.env['stock.location'].sudo().search([('barcode', "=", location_key)], limit=1)
        if not location:
            if(len(location_key) < 5):
                location = http.request.env['stock.location'].sudo().search([ ('id', '=', location_key) ], limit=1)
        if location:
            location_quants = self._get_location_quants(location)
            return {
                    'result': {
                        'location_id':location.id,
                        'name': location.name,
                        'complete_name': location.complete_name,
                        'display_name': location.display_name,
                        'barcode': location.barcode,
                        'products': location_quants
                    }
                }
        return {
            'error': {
                'message': "Location Not Found"
            }
        }

    @http.route('/barcode_scanner/get/locations', auth="public", methods=['POST'], website=True, type="json")
    def getLocations(self, token, **kw):
        if not http.request.env["res.users"].sudo().check_if_token_has_barcode_interface_access(token):
            return {
                'error':{
                    'message': 'Connection expired, try to login again.',
                    'logout': True
                }
            }
        location_ids = http.request.env["stock.location"].sudo().search([ ('usage', "=", 'internal') ])
        location_in_json_list = []
        for location_id in location_ids:
            location_in_json_list.append({
                'id': location_id.id,
                'name': location_id.name,
                'barcode': location_id.barcode,
                'display_name': location_id.display_name
            })
        return {
            'result': {
                'locations': location_in_json_list
            }
        }
    
    @http.route('/barcode_scanner/post/location/transfer', auth="public", methods=['POST'], website=True, type="json")
    def transfer(self, user_id, location_id, location_dest_id, product_ids_and_quants, token, **kw):
        if not http.request.env["res.users"].sudo().check_if_token_has_barcode_interface_access(token):
            return {
                'error':{
                    'message': 'Connection expired, try to login again.',
                    'logout': True
                }
            }
        picking_operation_type_internal_id = http.request.env.ref('stock.picking_type_internal').id

        picking = http.request.env['stock.picking'].sudo(user_id).create({
            'location_dest_id': location_dest_id,
            'location_id': location_id,
            'picking_type_id': picking_operation_type_internal_id,
        })
        
        if picking: 
            for product_id_and_quant in product_ids_and_quants:
                product = http.request.env['product.product'].sudo().search([('id', '=', product_id_and_quant['id'])])
                if product:
                    move = http.request.env['stock.move'].sudo(user_id).create({
                        'date': picking.date,
                        'date_expected': picking.date,
                        'location_dest_id': picking.location_dest_id.id,
                        'location_id': picking.location_id.id,
                        'name': '',
                        'product_uom': product.uom_id.id,
                        'product_uom_qty': product_id_and_quant['qty'],
                        'quantity_done': product_id_and_quant['qty'],
                        'product_id': product.id,
                        'picking_id': picking.id
                    })
                    if not move:
                        return {
                            'error': {
                                'message': "A move could not be created"
                            }
                        }
            picking.action_done()
            return {
                'result': {
                    'picking_id': picking.id,
                    'name': picking.display_name
                }
            }
        return {
            'error': {
                'message': "The picking could not be created"
            }
        }
    
    def _get_location_quants(self, location):
        location_quants = []
        for quant_id in location.quant_ids:
                quant = http.request.env['stock.quant'].sudo().search([ ('id', '=', quant_id.id) ])

                location_quants.append({
                    'product_id': quant.product_id.id,
                    'quantity': quant.quantity,
                    'reserved_quantity': quant.reserved_quantity,
                    'display_name': quant.display_name,
                    'barcode': quant.product_id.barcode,
                    'image': quant.product_id.image,
                    'name': quant.product_id.name,
                    'ref': quant.product_id.default_code
                })
        return location_quants