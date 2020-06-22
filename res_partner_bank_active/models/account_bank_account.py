from openerp import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)

class account_bank_account(models.Model):
    _inherit = ['res.partner.bank']
    active = fields.Boolean("Active", default=True)