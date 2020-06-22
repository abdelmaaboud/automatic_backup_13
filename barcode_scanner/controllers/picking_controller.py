# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import Response
import logging
import json
_logger = logging.getLogger(__name__)

class IncommingPickingsController(http.Controller):
    @http.route('/barcode_scanner/put/pickings/validate', auth="public", methods=['POST'], website=True, type="json")
    def validatePickings(self, picking_ids, token, **kw):
        # This method validate all the picking given inside the picking_ids param
        if not http.request.env["res.users"].sudo().check_if_token_has_barcode_interface_access(token):
            return {
                'error':{
                    'message': 'Connection expired, try to login again.',
                    'logout': True
                }
            }
        pickings = http.request.env["stock.picking"].sudo().search([ ('id', 'in', picking_ids), ('state', '!=', 'done') ])
        for picking in pickings:
            picking.action_done()

    @http.route('/barcode_scanner/put/picking/done', auth="public", methods=['POST'], website=True, type="json")
    def actionDonePicking(self, user_id, picking_key, moves, token, **kw):
        # This method call the action_done() method for one picking (picking_key)
        if not http.request.env["res.users"].sudo().check_if_token_has_barcode_interface_access(token):
            return {
                'error':{
                    'message': 'Connection expired, try to login again.',
                    'logout': True
                }
            }
        picking = http.request.env["stock.picking"].sudo().search([ ('id', '=', picking_key) ])
        if picking:
            for move in moves:
                for move_line in move["move_lines"]:
                    for picking_move_line in picking.move_line_ids:
                        if move_line["id"] == picking_move_line.id and int(move_line["selected"]) > 0:
                            picking_move_line.write({"qty_done": int(move_line["selected"])})
            picking.sudo(user_id).action_done()
            if picking.state == "done":
                return {
                    'result':{

                    }
                }
            else:
                return {
                    'error':{
                        'message': "Picking can not be validated"
                    }
                }
        return {
            'error':{
                'message': "Picking not found"
            }
        }


    @http.route('/barcode_scanner/get/partner/picking', auth="public", methods=['POST'], website=True, type="json")
    def getPartnerPicking(self, picking_key, token):
        # This method return all the pickings for 
        if not http.request.env["res.users"].sudo().check_if_token_has_barcode_interface_access(token):
            return {
                'error':{
                    'message': 'Connection expired, try to login again.',
                    'logout': True
                }
            }
        picking = http.request.env['stock.picking'].sudo().search([ ('id', '=', picking_key) ], limit=1)
        if picking:
            moves_in_json_list = []
            for move in picking.move_lines:
                move_lines = []
                if move.has_move_lines:
                    for move_line in move.move_line_ids:
                        move_lines.append({
                            'id': move_line.id,
                            'ordered_qty': move_line.ordered_qty,
                            'product_qty': move_line.product_qty,
                            'product_uom_qty': move_line.product_uom_qty,
                            'location': {
                                'id': move_line.location_id.id,
                                'name': move_line.location_id.name,
                                'display_name': move_line.location_id.display_name
                            }
                        })
                moves_in_json_list.append({
                    'id': move.id,
                    'product': {
                        'id': move.product_id.id,
                        'name': move.product_id.name,
                        'barcode': move.product_id.barcode,
                        'ref': move.product_id.default_code,
                        'image': move.product_id.image,
                    },
                    'ordered_qty': move.ordered_qty,
                    'reserved': move.reserved_availability,
                    'has_move_lines': move.has_move_lines,
                    'move_lines': move_lines
                })
            return {
                'result':{
                    'id': picking.id,
                    'name': picking.name,
                    'moves': moves_in_json_list,
                    'origin': picking.origin
                }
            }
        return {
            'error':{
                'message': 'Picking not found'
            }
        }



    @http.route('/barcode_scanner/get/product/picking', auth="public", methods=['POST'], website=True, type="json")
    def getPickingInfo(self, product_key, picking_key, token, **kw):
        # Return a picking base on the product_key and the picking_key
        # It will return moves that contains the product, so if the picking contains others moves but of different product, they will not be returned
        if not http.request.env["res.users"].sudo().check_if_token_has_barcode_interface_access(token):
            return {
                'error':{
                    'message': 'Connection expired, try to login again.',
                    'logout': True
                }
            }
        product = http.request.env['product.product'].sudo().search(
            [ '|', ('barcode', '=ilike', product_key), '|' ,('default_code', '=ilike', product_key), ('name', '=ilike', product_key) ],
             limit=1)
        if not product:
            return {
                'error': {
                    'message': "Product Not Found"
                }
            }
        incomming_picking = http.request.env['stock.picking'].sudo().search(
            [ '|', ('id', '=ilike', picking_key), ('name', '=ilike', picking_key) ],
            limit = 1
        )
        if not incomming_picking:
            return {
                'error': {
                    'message': "Picking Not Found"
                }
            }
        # Here we get all the moves base on the picking_id and the product_id
        incomming_picking_moves = http.request.env['stock.move'].sudo().search( # TO_DO : Picking already contains all the moves, so loop on those than search for moves
            [ ('product_id', '=', product.id), ('picking_id', '=', incomming_picking.id) ]
        )
        # Get all the ids of moves that we found
        incomming_picking_moves_lines_id = []
        for incomming_picking_move in incomming_picking_moves:
            incomming_picking_moves_lines_id.append(incomming_picking_move.id)

        # List that will be returned containing all the moves for a picking, 
        # If there is multiple moves for one product, we return only one move of this product
        incomming_picking_moves_list = []
        incomming_processed_products = [] # List of all the products that were already processed, it's there if there is multiples moves for the same product
        for incomming_picking_move in incomming_picking_moves:
            # Here we check that we did not processed the product, if not we will add it to the processed products
            if incomming_picking_move.product_id.id not in incomming_processed_products:
                incomming_picking_moves_list.append({
                    'id': incomming_picking_move.id,
                    'product_id': incomming_picking_move.product_id.id,
                    'ordered_qty': incomming_picking_move.ordered_qty,
                    'reserved': incomming_picking_move.reserved_availability,
                    'qty_done': incomming_picking_move.quantity_done
                })
                incomming_processed_products.append(incomming_picking_move.product_id.id)
            # If the product was already processed, we will change the quantities without adding the product in the moves list
            elif incomming_picking_move.product_id.id in incomming_processed_products:
                for incomming_move in incomming_picking_moves_list:
                        if incomming_move["product_id"] == incomming_picking_move.product_id.id:
                            incomming_move["ordered_qty"] += incomming_picking_move.ordered_qty
                            incomming_move["qty_done"] += incomming_picking_move.quantity_done
        
        return {
            'result': {
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'barcode': product.barcode,
                    'default_code': product.default_code,
                },
                'id': incomming_picking.id,
                'name': incomming_picking.name,
                'moves': incomming_picking_moves_list
            }
        }