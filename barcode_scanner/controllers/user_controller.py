# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import Response
import logging
import json
_logger = logging.getLogger(__name__)

class UserController(http.Controller):
    @http.route('/barcode_scanner/get/users', auth="public", methods=['POST'], website=True, type="json")
    def get_stock_users(self, **kw):
        return http.request.env["res.users"].sudo().get_stock_users()

    @http.route('/barcode_scanner/get/login', auth="public", methods=['POST'], website=True, type="json")
    def login(self, email, pin_code,**kw):
        try:
            user = http.request.env["res.users"].sudo().get_user_login_to_stock(email, pin_code)
            return {
                'result': {
                    'id': user.id,
                    'email': user.email,
                    'name': user.name,
                    'token': user.barcode_interface_token
                }
            }
        except Exception as e:
            return {
                'error':{
                    'message': str(e)
                }
            }