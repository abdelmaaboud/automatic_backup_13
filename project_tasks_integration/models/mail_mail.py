from odoo import models
import html2text

class mail_mail_utilities(models.Model):
    _inherit = ['mail.mail']
   
    def unescapeHTML(self, text):
        return html2text.html2text(text)
