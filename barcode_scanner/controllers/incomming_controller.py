# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import Response
import logging
import json
_logger = logging.getLogger(__name__)

class IncommingController(http.Controller):
    @http.route('/barcode_scanner/put/incomming/validate', auth="public", methods=['POST'], website=True, type="json")
    def validateIncommingPicking(self, user_id, picking_id, moves, token, **kw):
        # It will modify the moves of the picking with the moves given in the params
        # If the picking have all the moves validate, we will directly validate the picking
        if not http.request.env["res.users"].sudo().check_if_token_has_barcode_interface_access(token):
            return {
                'error':{
                    'message': 'Connection expired, try to login again.',
                    'logout': True
                }
            }

        incomming_picking = http.request.env['stock.picking'].sudo().search([ ('id', '=', picking_id) ], limit = 1)

        moves_product_id = []
        for move in moves:
            moves_product_id.append(move['product_id'])

        incomming_moves = http.request.env['stock.move'].sudo().search([ ('product_id', 'in', moves_product_id), ('picking_id', '=', picking_id) ])

        moves_lines_list_id = []
        for incomming_move in incomming_moves:
            moves_lines_list_id.append(incomming_move.id)


        incomming_move_lines = http.request.env['stock.move.line'].sudo().search([ ('move_id', 'in', moves_lines_list_id ) ])

        # We will modify all the moves by their quantity done attribute
        # But we will also modify the stock.quant to be sure that we can reserve the products directly 
        # -> We can't reserve products that are not in stock.quant and modify the done attribute for a move doesn't increment the stock.quant for the product...
        validated_move_ids = []
        for move_line in incomming_move_lines:
            for move in moves:
                selected_float = float(move["selected"])
                quant = http.request.env["stock.quant"].sudo().search([ ('product_id', '=', move_line.product_id.id),('location_id', '=', move_line.location_dest_id.id) ], limit=1)
                if move_line.qty_done + selected_float >= move_line.ordered_qty and move_line.qty_done != move_line.ordered_qty :
                    move_line_qty_done = move_line.qty_done
                    move_line.sudo().write({'qty_done': move_line.ordered_qty, 'qty_processed_on_barcode_interface': move_line.ordered_qty - move_line_qty_done})
                    quant._update_available_quantity(move_line.product_id, move_line.location_dest_id, move_line.ordered_qty - move_line_qty_done)
                    move["selected"] = selected_float - move_line.ordered_qty
                    if move_line.move_id.id not in validated_move_ids:
                        validated_move_ids.append(move_line.move_id.id)
                elif move_line.qty_done + selected_float < move_line.ordered_qty and move_line.qty_done + selected_float > 0:
                    move_line.sudo().write({'qty_done': move_line.qty_done + selected_float, 'qty_processed_on_barcode_interface': selected_float})
                    quant._update_available_quantity(move_line.product_id, move_line.location_dest_id, selected_float)
                    move["selected"] = selected_float - selected_float
                    if move_line.move_id.id not in validated_move_ids:
                        validated_move_ids.append(move_line.move_id.id)

        picking_move_lines = http.request.env['stock.move.line'].sudo().search([ ('picking_id', '=', incomming_picking.id) ])
        # We check if the picking moves are all done
        picking_completed = True
        for picking_move_line in picking_move_lines:
            if(picking_move_line.ordered_qty > picking_move_line.qty_done):
                picking_completed = False

        # If the picking is completed, we call the action_done method and remove by 1 from the stock.quant because action_done() will add all the moves in the stock.quant
        # If we do not update the quant by removing the moves, we will have the picking validated * 2
        if picking_completed:
            incomming_picking.sudo(user_id).action_done()
            # for move_line in incomming_picking.move_line_ids:
            #     quant = http.request.env["stock.quant"].sudo().search([ ('product_id', '=', move_line.product_id.id),('location_id', '=', move_line.location_dest_id.id) ], limit=1)
            #     quant._update_available_quantity(move_line.product_id, move_line.location_dest_id, float(move_line.qty_done) * -1)
            return {
                'result': {
                    'message': "",
                    'moves': validated_move_ids
                }
            }
        if len(validated_move_ids) > 0:
            return {
                'result': {
                    'message': "",
                    'moves': validated_move_ids
                }
            }