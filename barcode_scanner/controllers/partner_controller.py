# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import Response
import logging
import json
import math
_logger = logging.getLogger(__name__)

class PartnerController(http.Controller):
    @http.route('/barcode_scanner/get/partner', auth="public", methods=['POST'], website=True, type="json")
    def getPartner(self, partner_key, token, operation_type_name="", unwanted_states=[], **kw):
        # Return all the pickings for a partner based on the unwanted states and by operation type
        # If the operation type is 'in', then it will return all the incomming pickings by the partner key
        # If the operation type is 'out', then it will return all the outgoing pickings
        if not http.request.env["res.users"].sudo().check_if_token_has_barcode_interface_access(token):
            return {
                'error':{
                    'message': 'Connection expired, try to login again.',
                    'logout': True
                }
            }
        partner = http.request.env["res.partner"].sudo().search([ ('id', '=', partner_key) ], limit=1)
        if partner:
            picking_operation_type_id = http.request.env.ref("stock.picking_type_in").id
            if operation_type_name == "out":
                picking_operation_type_id = http.request.env.ref("stock.picking_type_out").id
            pickings = http.request.env["stock.picking"].sudo().search([ ('picking_type_id', '=', picking_operation_type_id), ('partner_id', '=', partner.id), ("state", 'not in', unwanted_states) ])
            pickings_list = []
            for picking in pickings:
                pickings_list.append({
                    'id': picking.id,
                    'name': picking.name,
                    'display_name': picking.display_name,
                    'partner_name': picking.partner_id.display_name,
                    'state': picking.state,
                    'origin': picking.origin
                })
            return {
                "result":{
                    'id': partner.id,
                    'name': partner.name,
                    'display_name': partner.display_name,
                    'property_stock_customer': partner.property_stock_customer.name,
                    'image': partner.image,
                    'street': partner.street,
                    'zip': partner.zip,
                    'city': partner.city,
                    'state': partner.state_id.name,
                    'country': partner.country_id.name,
                    'is_company': partner.is_company,
                    'is_employee': partner.employee,
                    'is_customer': partner.customer,
                    'is_vendor': partner.supplier,
                    'pickings': pickings_list
                }
            }
        else:
            return{
                'error':{
                    'message': "Partner not found"
                }
            }

    @http.route('/barcode_scanner/post/partner/transfer', auth="public", methods=['POST'], website=True, type="json")
    def createPickingOut(self, user_id, partner_key, products, token, **kw):
        # Create a transfer from the stock to the partner
        if not http.request.env["res.users"].sudo().check_if_token_has_barcode_interface_access(token):
            return {
                'error':{
                    'message': 'Connection expired, try to login again.',
                    'logout': True
                }
            }
        if len(products) <= 0:
            return {
                'error': {
                    'message': 'No products selected'
                }
            }
        picking_operation_type_internal_id = http.request.env.ref('stock.picking_type_out').id
        company_stock_location_id = http.request.env.ref("stock.stock_location_stock").id
        partner = http.request.env["res.partner"].sudo().search([ ('id', '=', partner_key) ], limit = 1)

        picking = http.request.env['stock.picking'].sudo(user_id).create({
            'partner_id': partner.id,
            'location_id': company_stock_location_id,
            'location_dest_id': partner.property_stock_customer.id,
            'picking_type_id': picking_operation_type_internal_id,
        })

        if picking:
            for product in products:
                product_in_odoo = http.request.env['product.product'].sudo().search([ ('id', '=', product['id']) ], limit=1)
                for quant in product["quants"]:
                    move = http.request.env['stock.move'].sudo(user_id).create({
                            'date': picking.date,
                            'date_expected': picking.date,
                            'location_dest_id': picking.location_dest_id.id,
                            'location_id': quant["location_id"],
                            'name': '',
                            'product_uom': product_in_odoo.uom_id.id,
                            'product_uom_qty': quant['selected'],
                            'quantity_done': quant['selected'],
                            'product_id': product['id'],
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
                    'id': picking.id,
                    'name': picking.display_name
                }
            }
        return {
            'error': {
                'message': "The picking could not be created"
            }
        }

    @http.route('/barcode_scanner/get/partners', auth="public", methods=['POST'], website=True, type="json")
    def getPartners(self, token, page, search_text=None, is_company=True, is_vendor=True, is_customer=True, is_employee=True, limit=50, **kw):
        # Return all the partners 
        if not http.request.env["res.users"].sudo().check_if_token_has_barcode_interface_access(token):
            return {
                'error':{
                    'message': 'Connection expired, try to login again.',
                    'logout': True
                }
            }
            
        offset = (page - 1) * limit
        
        domain = []
        if not is_company:
            domain.append(('is_company', '=', False))
        if not is_vendor:
            domain.append(('supplier', '=', False))
        if not is_customer:
            domain.append(('customer', '=', False))
        if not is_employee:
            domain.append(('employee', '=', False))
        #if search_text:
            #domain.append(('name', 'ilike', search_text))
        partners = http.request.env["res.partner"].sudo().search(domain, offset=offset, limit=limit)
        if search_text:
            partners = partners.filtered(lambda partner: partner.display_name.lower().find(search_text.lower()) != -1)
        
        # Get total pages based by number of partners
        total_partners = http.request.env["res.partner"].sudo().search(domain)
        if search_text:
            total_partners = total_partners.filtered(lambda partner: partner.display_name.lower().find(search_text.lower()) != -1)
        total_pages = math.ceil(float(len(total_partners))/limit)

        partner_list = []

        for partner in partners:
            partner_list.append({
                'id': partner.id,
                'name': partner.name,
                'display_name': partner.display_name,
                'image': partner.image,
                'company_name': partner.company_name,
                'company_type': partner.company_type,
                'is_company': partner.is_company,
                'is_employee': partner.employee,
                'is_customer': partner.customer,
                'is_vendor': partner.supplier,
                'parent_id': partner.parent_id.id,
                'address': {
                    'country': partner.country_id.name,
                    'city': partner.city,
                    'zip': partner.zip,
                    'state': partner.state_id.name
                }
            })

        return {
            'result':{
                'partners': partner_list,
                'total_pages': total_pages
            }
        }
