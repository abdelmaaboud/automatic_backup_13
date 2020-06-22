# -*- coding: utf-8 -*-
from odoo import models,fields, api, _

import logging
_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    state = fields.Selection([('obsolete', 'Obsolete'), ('sellable', 'Sellable')], "State", default='sellable')
