from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    send_attachments = fields.Boolean(string="Send auto attachments", default=True)
