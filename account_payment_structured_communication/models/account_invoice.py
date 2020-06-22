from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    supplier_reference = fields.Char(string="Supplier reference")
