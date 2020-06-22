# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


import logging
_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = ['res.users']
    
    automatically_assign_to_created_task = fields.Boolean(string="Automatically Assign Me To Task Created By Me", 
                                                          help="When you will create a new task, the user assigned to the task will automatically be you.")