# -*- coding: utf-8 -*-

from odoo import api, models, fields, _


class SaleSubscription(models.Model):
    _inherit = 'sale.subscription'

    lead_id = fields.Many2one('crm.lead', 'CRM Lead')
