# -*- coding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions SARL
# in Luxembourg 2018

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class Page(models.Model):
    _name = 'project.smart.display.page'
    _order = 'name'

    name = fields.Char(required=True, string="Name")
    mode = fields.Selection([('iframe', 'Iframe'), ('smart_dashboard', 'Smart Dashboard')], string="Mode", required=True)
    iframe_url = fields.Char(string="Iframe URL")
    widget_line_ids = fields.One2many('project.smart.display.page.widget.line', 'page_id', string="Widgets")