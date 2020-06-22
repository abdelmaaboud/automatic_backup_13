# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class MoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.multi
    def _prepare_payment_line_vals(self, payment_order):
        values = super(MoveLine, self)._prepare_payment_line_vals(payment_order)
        values.update({'send_remittance_advice': self.partner_id.send_remittance_advice})
        return values
