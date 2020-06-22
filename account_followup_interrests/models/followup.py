# -*- coding: utf-8 -*-
from odoo import models, fields, api

import logging
_logger = logging.getLogger(__name__)
    
class AccountFollowupFollowup(models.Model):
    _inherit = ['account_followup.followup']

    late_interest_percentage = fields.Integer(string="Late interest (%)")
    late_allowance = fields.Float(string="Late allowance")

class AccountFollowupFollowupLine(models.Model):
    _inherit = ['account_followup.followup.line']

    compute_interests = fields.Boolean(string="Compute interests")
    compute_allowance = fields.Boolean(string="Compute allowance")
