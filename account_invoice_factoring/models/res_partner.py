# -*- coding: utf-8 -*-

from odoo import models, fields, api

import logging
_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = ['res.partner']

    do_factoring = fields.Boolean(string="Do factoring", default=False)


