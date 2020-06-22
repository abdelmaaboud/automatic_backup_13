# -*- coding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions SARL
# in Luxembourg 2018

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class DisplayPageLine(models.Model):
    _name = 'project.smart.display.page.line'
    _order = 'sequence'

    display_id = fields.Many2one('project.smart.display')
    page_id = fields.Many2one('project.smart.display.page', string= "Name")
    name = fields.Char(related='page_id.name')
    mode = fields.Selection(related='page_id.mode')
    iframe_url = fields.Char(related='page_id.iframe_url')
    widget_line_ids = fields.One2many(related='page_id.widget_line_ids')
    sequence = fields.Integer(default=1)