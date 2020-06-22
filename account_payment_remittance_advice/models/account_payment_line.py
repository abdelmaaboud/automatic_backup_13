# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class PaymentOrderLine(models.Model):
    _inherit = 'account.payment.line'

    send_remittance_advice = fields.Boolean(default=lambda self: self.get_default_send_remittance_advice())

    @api.model
    def get_default_send_remittance_advice(self):
        return self.partner_id.send_remittance_advice

    @api.model
    def _send_remittance_advice_mail(self):
        template_id = self.env['mail.template'].search([("name", "=", "Remittance Advice Email")])
        if template_id:
            mail_message = template_id.send_mail(self.id)
