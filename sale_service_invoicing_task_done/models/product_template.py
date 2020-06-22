from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = ['product.template']

    invoice_policy = fields.Selection(selection_add=[('task', 'Invoice based on sold Task when set to done')])
