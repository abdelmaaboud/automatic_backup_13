# -*- coding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions SARL
# in Luxembourg 2018

from odoo import models, fields, api, exceptions, _
from odoo.addons.website.models.website import slugify
from odoo.exceptions import UserError
from odoo.http import request

import uuid
import requests
import logging
_logger = logging.getLogger(__name__)

class Display(models.Model):
    _name = 'project.smart.display'
    _inherit = ['website.published.mixin']
    _order = "raspberry_ip_address, name"

    def _get_default_token(self):
        return uuid.uuid4().hex

    name = fields.Char(required=True, string="Name")
    raspberry_ip_address = fields.Char(string="Raspberry's IP address")
    user_id = fields.Many2one('res.users', string="User", required=True)
    active = fields.Boolean(string="Active", default=True)
    page_line_ids = fields.One2many('project.smart.display.page.line', 'display_id', string="Pages")
    delay = fields.Integer(string="Delay (s)", default=15)
    token = fields.Char(default=lambda self: self._get_default_token())
    url_for_pi = fields.Char(compute='_get_url_for_pi')
    show_telephony = fields.Boolean(string="Show telephony")
    callflow_ids = fields.Many2many('project.smart.display.callflow', string="Contacts to show", help="Shows status of selected contacts")

    @api.onchange('delay')
    def _check_delay_superior_to_nine(self):
        if self.delay < 10:
            self.delay = 10
            return {
                'warning': {
                    'title': _("Delay not in range"),
                    'message': _("Delay must be superior to 9"),
                },
            }

    @api.multi
    def _get_url_for_pi(self):
        base_url = self.env['ir.config_parameter'].search([('key', '=', 'web.base.url')])
        if len(base_url) > 0:
            for display in self:
                display.url_for_pi = base_url.value + display.website_url + '?token=' + display.token

    @api.multi
    def _compute_website_url(self):
        super(Display, self)._compute_website_url()
        for display in self:
            display.website_url = "/smartdisplay/display/%s" % (slugify(display))

    @api.multi
    def website_open_page_button(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': self.url_for_pi,
            'target': 'new',
        }
    
    def _request_to_get_callflows_from_API(self):
        url = "https://abakus-office.allocloud.com/v3.0/auth/user"
        data = {
            "data": {
                "username": "shaheen.kourdlassi@abakusitsolutions.eu",
                "api_key": "pD-ReHXhDGQddV3DhuYDM0-qCEBAVDuaptqYpdD5KcBnCpyANJmOzA"
            }
        }
        response = requests.put(url, json=data) # get auth_token
        
        url = "https://abakus-office.allocloud.com/v3.0/callflows"
        headers = {
            'Content-Type': 'application/json',
            'X-Auth-Token': response.json()['auth_token']
        }
        return requests.get(url, headers=headers) # get all callflows
    
    @api.multi
    def create_callflows_in_DB(self):
        response = self._request_to_get_callflows_from_API()
        
        data_ids = request.env['project.smart.display.callflow'].sudo().search([])
        callflow_exists = False
        if len(data_ids) > 0: # callflow(s) already exist(s) in database
            for callflow in response.json()['data']: # allows adding callflows who don't exist in database
                if callflow['featurecode'] == False: # allows taking valid contacts only
                    for data in data_ids:
                        if callflow['name'] == data.name:
                            callflow_exists = True
                    if callflow_exists == False:
                        self.env['project.smart.display.callflow'].create({'name': callflow['name'], 'number': callflow['numbers'][0]})
            
            callflow_exists = False
            for data in data_ids: # allows deleting callflows who no longer exist in API request
                for callflow in response.json()['data']:
                    if callflow['featurecode'] == False and data.name == callflow['name']:
                        callflow_exists = True
                if callflow_exists == False:
                    self.env["project.smart.display.callflow"].sudo().search(['name', '=', callflow['name']]).unlink()
        else:
            for callflow in response.json()['data']:
                if callflow['featurecode'] == False: # allows taking valid contacts only
                    self.env['project.smart.display.callflow'].create({'name': callflow['name'], 'number': callflow['numbers'][0]})