# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import Response
import logging
import json
_logger = logging.getLogger(__name__)

class OutGoingsController(http.Controller):
    @http.route('/barcode_scanner/put/outgoing/validate', auth="public", methods=['POST'], website=True, type="json")
    def validateOutgoingPicking(self, user_id, picking_key, product_key, moves, token, **kw):
        # This method validate the moves for a picking but not the picking itself
        # For the moves given in the params, it will update the moves in Odoo
        # It is working on moves specifically on the product key that is given in the params
        if not http.request.env["res.users"].sudo().check_if_token_has_barcode_interface_access(token):
            return {
                'error':{
                    'message': 'Connection expired, try to login again.',
                    'logout': True
                }
            }
        picking = http.request.env['stock.picking'].sudo().search([ ('id', '=', picking_key) ])

        for move in picking.move_lines:
            if move.product_id.id == product_key or move.product_id.barcode == product_key or move.product_id.name == product_key:
                if not move.has_move_lines:
                    move_line = http.request.env['stock.move.line'].sudo(user_id).create({
                                'date': picking.date,
                                'date_expected': picking.date,
                                'move_id': move.id,
                                'location_dest_id': picking.location_dest_id.id,
                                'location_id': picking.location_id.id,
                                'product_uom_id': move.product_uom.id,
                                'product_uom_qty': float(moves[0]['selected']),
                                'product_id': move.product_id.id,
                                'picking_id': picking.id,
                                'ordered_qty': float(moves[0]['selected'])
                            })
                    quant = http.request.env["stock.quant"]
                    # After the move_line creation, we update the reserved quantity in the stock.quant of the product
                    quant._update_reserved_quantity(move.product_id, move.location_id, float(moves[0]['selected']))

                    if move_line:
                        return {
                            'result': {
                                'message': "Confirmed"
                            }
                        }
                else:
                    for move_line in move.move_line_ids:
                        if float(moves[0]['selected']) > 0:
                            quant = http.request.env["stock.quant"].sudo().search([ ('product_id', '=', move_line.product_id.id),('location_id', '=', move_line.location_id.id) ], limit=1)
                            if quant.quantity - quant.reserved_quantity > 0:
                                if quant.reserved_quantity + float(moves[0]['selected']) <= quant.quantity:
                                    move_line_product_uom_qty_before_update = move_line.product_uom_qty
                                    move_line.write({'product_uom_qty': move_line.product_uom_qty + float(moves[0]['selected'])})
                                    if move_line_product_uom_qty_before_update > 0:
                                        quant._update_reserved_quantity(move_line.product_id, move_line.location_id, float(moves[0]['selected']))
                                    moves[0]["selected"] = float(moves[0]["selected"]) - float(moves[0]["selected"])
                                elif quant.reserved_quantity + float(moves[0]['selected']) > quant.quantity:
                                    move_line.write({'product_uom_qty': quant.quantity })
                                    if move_line_product_uom_qty_before_update > 0:
                                        quant._update_reserved_quantity(move_line.product_id, move_line.location_id, float(moves[0]['selected']))
                                    moves[0]['selected'] = float(moves[0]['selected']) - quant.quantity
                    if float(moves[0]['selected']) > 0: # If there is still some selected products we create a new move_line
                        _logger.debug("creating new move line")
                        move_line = http.request.env['stock.move.line'].sudo(user_id).create({
                                    'date': picking.date,
                                    'date_expected': picking.date,
                                    'move_id': move.id,
                                    'location_dest_id': move.location_dest_id.id,
                                    'location_id': move.location_id.id,
                                    'product_uom_id': move.product_uom.id,
                                    'product_uom_qty': float(moves[0]['selected']),
                                    'product_id': move.product_id.id,
                                    'picking_id': picking.id,
                                    'ordered_qty': float(moves[0]['selected'])
                                })
                        quant = http.request.env["stock.quant"]
                        # After the move_line creation, we update the reserved quantity in the stock.quant of the product
                        quant._update_reserved_quantity(move.product_id, move.location_id, float(moves[0]['selected']))


                    return {
                        'result':{
                            'message': "Confirmed"
                        }
                    }
            