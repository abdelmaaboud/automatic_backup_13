from odoo import models, fields

class ResCountry(models.Model):
    _inherit = ['res.country']
    
    selectable_for_applicant = fields.Boolean(string="Selectable for applicants", default=False)