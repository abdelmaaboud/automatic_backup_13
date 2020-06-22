# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
import logging
_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = ['res.partner']

    payments_sum_of_interests = fields.Float(compute="_compute_payments_sum_of_interests", string="Sum of due interests")
    payments_sum_of_allowances = fields.Float(compute="_compute_payments_sum_of_allowances", string="Sum of due allowances")
    payments_sum_due = fields.Float(compute="_compute_payments_sum_due", string="Total amount due")

    @api.multi
    def _compute_payments_sum_of_interests(self):
        for partner in self:
            if len(partner.unreconciled_aml_ids) > 0:
                interests = 0
                for line in partner.unreconciled_aml_ids:
                    interests = interests + line.payments_interests
                partner.payments_sum_of_interests = interests

    @api.multi
    def _compute_payments_sum_of_allowances(self):
        for partner in self:
            if len(partner.unreconciled_aml_ids) > 0:
                allowances = 0
                for line in self.unreconciled_aml_ids:
                    allowances = allowances + line.payments_allowances
                partner.payments_sum_of_allowances = allowances

    @api.multi
    def _compute_payments_sum_due(self):
        for partner in self:
            partner.payments_sum_due = partner.payment_amount_due + partner.payments_sum_of_interests + partner.payments_sum_of_allowances
