# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class PaymentOrder(models.Model):
    _inherit = 'account.payment.order'

    """
        Overrides method in order to auto-send an
        email to the partners whom have the 'Send Remittance Advice' checked
    """

    @api.multi
    def generated2uploaded(self):
        check = super(PaymentOrder, self).generated2uploaded()
        if check:
            for line in self.payment_line_ids:
                if line.send_remittance_advice:
                    _logger.debug("SEND REMITTANCE")
                    line._send_remittance_advice_mail()
        return True
