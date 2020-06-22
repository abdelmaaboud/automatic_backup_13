# (c) AbAKUS IT Solutions
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    is_shipped = fields.Boolean(store=True)
