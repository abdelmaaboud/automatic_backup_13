# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountAnalyticTeam(models.Model):
    _name = 'account.analytic.account.team'
    
    name = fields.Char(string="Name", required=True, translate=True)
    company_id = fields.Many2one('res.company', string="Company")
    active = fields.Boolean(string="Active", default=True)
    users = fields.Many2many('res.users', string="Members")
