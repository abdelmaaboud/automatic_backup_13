# -*- coding: utf-8 -*-
from odoo import fields, models, api, exceptions, _
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    sales_count = fields.Integer(store=True)