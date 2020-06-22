# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = 'res.partner'

    send_remittance_advice = fields.Boolean(default=False)
