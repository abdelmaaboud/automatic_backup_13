# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ResPartner(models.Model):
    _inherit = ['res.partner']

    open_projects_count = fields.Integer(string="Projects", compute="_compute_open_projects")

    @api.multi
    def _compute_open_projects(self):
        for partner in self:
            partner.open_projects_count = self.env['project.project'].search_count([('partner_id', '=', partner.id)])