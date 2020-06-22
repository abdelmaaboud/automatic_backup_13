# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _

import logging
_logger = logging.getLogger(__name__)
    
    
class HrHolidaysStatus(models.Model):
    _inherit = 'hr.holidays.status'
    _order = 'sequence, id'

    sequence = fields.Integer(string='Sequence', default=10)
