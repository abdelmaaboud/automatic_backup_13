from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    company_attachment_ids = fields.One2many('res.company.attachment', 'company_id')
