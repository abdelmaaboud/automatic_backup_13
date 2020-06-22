from odoo import models, fields

class HrApplicant(models.Model):
    _inherit = ['hr.applicant']
    
    country_ids = fields.Many2many('res.country', string="Countries", domain=[('selectable_for_applicant', '=', True)])
    