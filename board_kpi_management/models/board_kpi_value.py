# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
from odoo import tools

from datetime import datetime
import logging
_logger = logging.getLogger(__name__)

class BoardKPIValue(models.Model):
    """
    KPI
    """
    _name = 'board.kpi.value'
    _description = 'KPI value'
    _order = "create_date desc"

    kpi_id = fields.Many2one('board.kpi', string="KPI", ondelete='cascade')
    value = fields.Float(string="Value")
    value_boolean = fields.Boolean(string="Boolean value")
    value_type = fields.Selection(related='kpi_id.value_type', string="Value type")
    custom_create_date = fields.Datetime(default=lambda self: fields.datetime.now())
    agregation_type = fields.Char(string="Agregation type", default="Not agregated")