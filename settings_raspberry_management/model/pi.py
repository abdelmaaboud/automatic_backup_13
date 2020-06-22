# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solution
from odoo import models, fields, api


class RaspberryPi(models.Model):

    _name = 'settings.raspberry_pi'

    name = fields.Char()
    ip_address = fields.Char(string='IP Address')

    webpage_url = fields.Char(string='Webpage to load')
    webpage_user = fields.Char()
    webpage_password = fields.Char()
