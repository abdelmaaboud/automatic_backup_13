from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)

class PaymentOrderLine(models.Model):
    _inherit = 'account.payment.line'

    communication_type = fields.Selection([
        ('normal', 'Free'),
        ('bba', 'Structured'),
        ('ISO', 'ISO'),
        ], string='Communication Type', required=True, default='normal')

    def invoice_reference_type2communication_type(self):
        res = super(PaymentOrderLine, self).invoice_reference_type2communication_type()
        res.update({'bba': 'bba'})
        return res
