# -*- coding: utf-8 -*-

from odoo import models, fields, api

import logging
_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = ['res.company']

    factoring_text = fields.Html("Factoring text for invoices", translate=True)


