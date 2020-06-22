# -*- coding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions SARL
# in Luxembourg 2018

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class WidgetFieldsLine(models.Model):
    _name = 'project.smart.display.widget.fields.line'
    _order = 'sequence'

    widget_id = fields.Many2one('project.smart.display.widget')
    model = fields.Char(related='widget_id.model')
    field_id = fields.Many2one('ir.model.fields', string="Columns to display in the list")
    sequence = fields.Integer(default=1)