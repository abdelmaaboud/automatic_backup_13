# -*- coding: utf-8 -*-

from odoo import models, fields, api


import logging
_logger = logging.getLogger(__name__)

class account_analytic_account_improvements(models.Model):
    _inherit = 'account.analytic.account'

    first_subscription_id = fields.Many2one(comodel_name='sale.subscription', string="Subscription", compute='_compute_first_subscription')

    @api.one
    def _compute_first_subscription(self):
        if self.subscription_ids and len(self.subscription_ids) > 0 :
            self.first_subscription_id = self.subscription_ids[0]


