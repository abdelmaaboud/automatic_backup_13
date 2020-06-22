from odoo import models, fields

class ResCompanyAttachment(models.Model):
    _name = 'res.company.attachment'

    name = fields.Char(required=True)
    company_id = fields.Many2one('res.company', required=True)
    lang_id = fields.Many2one('res.lang', string="Language")
    attachments_ids = fields.Many2many('ir.attachment', string="Attachments")
    mail_template_ids = fields.Many2many('mail.template', string="Email Templates")
    
