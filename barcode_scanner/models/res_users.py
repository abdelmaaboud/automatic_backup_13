# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
import datetime
import logging
import time
from secrets import token_hex
_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = 'res.users'

    pin_code = fields.Integer(string = "Pin Code")
    has_barcode_interface_access = fields.Boolean(string = "Has Barcode Interface Access", default=False)
    barcode_interface_token = fields.Char('Barcode Interface Token', default='')
    barcode_interface_timeout = fields.Integer('Timeout Timestamp')

    def get_stock_users(self):
        users = self.search([('has_barcode_interface_access', '=', True)])
        my_user_list = []
        for user in users:
            user_info = {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'image': user.image
            }
            my_user_list.append(user_info)
        return {'users': my_user_list}

    @api.multi
    def get_user_login_to_stock(self, email, pin_code):
        user = self.search([ ("email", '=', email), ("pin_code", '=', pin_code), ("has_barcode_interface_access", '=', True) ], limit = 1)
        if not user:
            raise Exception(_('User or pin code incorrect'))
        user.generate_barcode_interface_token()
        return user

    @api.one
    def generate_barcode_interface_token(self):
        self.barcode_interface_token = token_hex(16)
        self.set_barcode_interface_timeout(30)
        _logger.debug(self.barcode_interface_token)

    @api.multi
    def check_if_token_has_barcode_interface_access(self, token):
        user = self.search([ ('barcode_interface_token', '=', token) ], limit=1)
        if user and user.barcode_interface_timeout > int(datetime.datetime.now().timestamp()):
            user.set_barcode_interface_timeout(30)
            return True
        return False

    @api.one
    def set_barcode_interface_timeout(self, minutes):
        now = datetime.datetime.now()
        now_plus_minutes = now + datetime.timedelta(minutes = minutes)
        now_plus_minutes_in_int = now_plus_minutes.timestamp()
        self.write({
            'barcode_interface_timeout': now_plus_minutes_in_int
        })
