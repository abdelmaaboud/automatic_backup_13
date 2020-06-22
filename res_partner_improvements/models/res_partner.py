# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ProjectProject(models.Model):
    _inherit = ['res.partner']

    street = fields.Char(track_visibility='onchange')
    street2 = fields.Char(track_visibility='onchange')
    city = fields.Char(track_visibility='onchange')
    zip = fields.Char(track_visibility='onchange')
    zip = fields.Char(track_visibility='onchange')
    state_id = fields.Many2one(track_visibility='onchange')
    country_id = fields.Many2one(track_visibility='onchange')

    def archive(self):
        self.write({'active': False})
        
        
    @api.model
    def create(self, vals):
        if "parent_id" in vals and vals['parent_id']:
            parent_id = self.env['res.partner'].browse(vals['parent_id'])
            if parent_id.lang:
                vals.update({
                    'lang': parent_id.lang
                })
        return super(ProjectProject, self).create(vals)