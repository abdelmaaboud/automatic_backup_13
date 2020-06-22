# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.translate import _

import logging
_logger = logging.getLogger(__name__)

class AnalyticAccountLine(models.Model):
    _inherit = 'account.analytic.line'
    
    note_to_manager_exists = fields.Boolean(string="Note To Manager", compute="_compute_note_to_manager_exists")
    
    @api.depends('note_to_manager')
    def _compute_note_to_manager_exists(self):
        for line in self:
            if line.note_to_manager:
                line.note_to_manager_exists = True
            else:
                line.note_to_manager_exists = False