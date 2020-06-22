# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def write(self, vals):
        if 'expected_pay_date' in vals:
            vals['date_maturity'] = vals['expected_pay_date']
            if self.invoice_id:
                self.invoice_id.write({'date_due': vals['expected_pay_date']})
            self.move_id.line_ids.filtered(lambda l: l.id != self.id).write({'date_maturity': vals['expected_pay_date']})
        return super(AccountMoveLine, self).write(vals)
