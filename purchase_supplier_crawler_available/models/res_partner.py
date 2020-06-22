# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _

import logging
_logger = logging.getLogger(__name__)
    
    
class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    crawler_available = fields.Boolean(string="Crawler Available", default=False, help="Check this box if the ChromeWeb App is available for this supplier")