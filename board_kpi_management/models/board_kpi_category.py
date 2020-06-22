# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
from odoo import tools

import logging
_logger = logging.getLogger(__name__)

class BoardKPICategory(models.Model):
    """
    KPI
    """
    _name = 'board.kpi.category'
    _description = 'KPI category'
    _order = "name"

    name = fields.Char(string="Name")
