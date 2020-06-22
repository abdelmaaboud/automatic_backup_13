# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import Response
from odoo import models, fields, api, exceptions, _
import logging
import json
import math
_logger = logging.getLogger(__name__)

class ProductController(http.Controller):
    @http.route('/barcode_scanner/put/product/', auth="public", methods=['POST'], website=True, type="json")
    def editProduct(self, product, token, **kw):
        if not http.request.env["res.users"].sudo().check_if_token_has_barcode_interface_access(token):
            return {
                'error':{
                    'message': 'Connection expired, try to login again.',
                    'logout': True
                }
            }
        # Search product in Odoo
        product_in_db = http.request.env["product.product"].sudo().search([ ("id", "=", int(product['id'])) ])
        product_template_in_db = http.request.env["product.template"].sudo().search([ ("id", "=", int(product['id'])) ])
        # Check if barcode already used
        product_barcode = http.request.env["product.product"].sudo().search([('barcode', '=', product['barcode']), ('id', '!=', product["id"])])
        if product_barcode:
            return {
                'error': {
                    'message': _("This barcode is already used")
                }
            }
        # Modify the product found in Odoo with the product json given
        if product["barcode"] == "":
            product["barcode"] = None
        if product["description"] == "":
            product["decription"] = None
        if product["ref"] == "":
            product["ref"] = None
        product_in_db.write({'name': product['name'], 'barcode': product['barcode'], 'default_code': product['ref'], 'description': product["description"] })
        product_template_in_db.write({'image': product["image"]})
        return {
            'result':{

            }
        }
    
    @http.route('/barcode_scanner/get/products', auth="public", methods=['POST'], website=True, type="json")
    def getAllProducts(self, token, page, search_text=None, show_available=True, show_unavailable=True, limit=50, **kw):
        if not http.request.env["res.users"].sudo().check_if_token_has_barcode_interface_access(token):
            return {
                'error':{
                    'message': 'Connection expired, try to login again.',
                    'logout': True
                }
            }
        # Compute the offset based on the actual page and limit
        offset = (page - 1) * limit
        
        # Domain creation
        domain = [('type', '=', 'product')]
        if not show_unavailable:
            domain.append(('qty_available', '>', 0))
        if not show_available:
            domain.append(('qty_available', '<', 1))
        if search_text:
            domain.append('|')
            domain.append(('name', 'ilike', search_text))
            domain.append('|')
            domain.append('&')
            domain.append(('default_code', '!=', False))
            domain.append(('default_code', 'ilike', search_text))
            domain.append('|')
            domain.append(('barcode', 'ilike', search_text))
            domain.append(('description', 'ilike', search_text))
        # Get total products
        products = http.request.env["product.product"].sudo().search(domain, offset=offset, limit=limit)
        
        # Get total pages based by number of partners
        total_products = http.request.env["product.product"].sudo().search_count(domain)
        total_pages = math.ceil(float(total_products)/limit)

        product_list = [] # A list in JSON with attributes that we want
        for product in products:
            # Here we check how much reservation there is for a product and then we check the final availability
            reserved_quantity = 0
            for stock_quant in product.stock_quant_ids:
                if stock_quant.location_id.usage == "internal":
                    reserved_quantity += stock_quant.reserved_quantity
            available_quantity = product.qty_available - reserved_quantity
            # Adding product attributes to product list
            product_list.append({
                'id': product.id,
                'name': product.name,
                'display_name': product.display_name,
                'ref': product.code,
                'description': product.description,
                'barcode': product.barcode,
                'image': product.image,
                'available_quantity': available_quantity
            })

        return {
            'result':{
                'products': product_list,
                'total_pages': total_pages
            }
        }

    @http.route('/barcode_scanner/get/product', auth="public", methods=['POST'], website=True, type="json")
    def getProduct(self, product_key, token, operation_type_name=None, **kw):
        # This method return a product with its picking by operation type.
        # The operation type can be 'in' or 'out'.
        # If it's 'in', then all the pickings will be incomming pickings for the product that we want (given by the product_key)
        # And if it's 'out', then all the picking will be outgoing pickings
        if not http.request.env["res.users"].sudo().check_if_token_has_barcode_interface_access(token):
            return {
                'error':{
                    'message': 'Connection expired, try to login again.',
                    'logout': True
                }
            }
        # Find product by it's name, barcode or id with the product key given
        product = None
        if isinstance(product_key, int):
            product = http.request.env['product.product'].sudo().search(
                [ '|', ('barcode', '=ilike', product_key), '|' ,('id', '=ilike', product_key), ('name', '=ilike', product_key) ],
                limit=1)
        else:
            product = http.request.env["product.product"].sudo().search(
                [ '|', ('barcode', '=ilike', product_key), ('name', '=ilike', product_key) ], limit=1
            )
        product_reserved_quant = 0
        product_stock_quant_list = [] # This list will contain all the quantity of one product present by internal location
        for stock_quant in product.stock_quant_ids:
            if stock_quant.location_id.usage == "internal":
                product_reserved_quant += stock_quant.reserved_quantity
                product_stock_quant_list.append({
                    'id': stock_quant.id,
                    'location_id': stock_quant.location_id.id,
                    'location_display_name': stock_quant.location_id.display_name,
                    'quantity_available': stock_quant.quantity,
                    'reserved_quantity': stock_quant.reserved_quantity
                })
        if product:
            # We check here the operation type name (in or out)
            picking_in_operation_type_id = http.request.env.ref("stock.picking_type_in").id
            if operation_type_name == "out":
                picking_in_operation_type_id = http.request.env.ref("stock.picking_type_out").id
            moves = http.request.env['stock.move'].sudo().search([ ('product_id', '=', product.id), 
            ('picking_id.picking_type_id', '=', picking_in_operation_type_id ) ])
            picking_list = []
            treated_pickings = []
            for move in moves:
                # We get all the moves and then check if their picking parent is done or canceled
                if ((move.ordered_qty > move.quantity_done and operation_type_name == "in") 
                    or (operation_type_name == "out" and move.product_uom_qty > move.reserved_availability)):
                    if (move.picking_id.id not in treated_pickings and
                        move.picking_id.state != 'done' and move.picking_id.state != 'cancel'):
                        picking_list.append({
                            'id': move.picking_id.id,
                            'name': move.picking_id.name,
                            'display_name': move.picking_id.display_name,
                            'partner_name': move.picking_id.partner_id.display_name,
                            'ordered_qty': move.ordered_qty,
                            'origin': move.picking_id.origin,
                            'state': move.picking_id.state
                        })
                        treated_pickings.append(move.picking_id.id)
                    elif move.picking_id.id in treated_pickings:
                        for picking in picking_list:
                            if picking["id"] == move.picking_id.id:
                                picking["ordered_qty"] += move.ordered_qty
            return {
                    'result': {
                        'id':product.id,
                        'name': product.name,
                        'ref': product.code,
                        'display_name': product.display_name,
                        'description': product.description,
                        'qty_available': product.qty_available,
                        'reserved_quantity': product_reserved_quant,
                        'barcode': product.barcode,
                        'image': product.image,
                        'incoming_qty': product.incoming_qty,
                        'outgoing_qty': product.outgoing_qty,
                        'pickings': picking_list,
                        'quants': product_stock_quant_list
                    }
                }
        return {
            'error': {
                'message': "Product Not Found"
            }
        }