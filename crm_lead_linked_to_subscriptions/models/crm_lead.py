# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class Lead(models.Model):
    _inherit = 'crm.lead'

    subscription_count = fields.Integer(compute='_compute_subscription_count')

    def _compute_subscription_count(self):
        subscription = self.env['sale.subscription']
        for lead in self:
            lead.subscription_count = subscription.search_count([('lead_id', '=', lead.id)])
