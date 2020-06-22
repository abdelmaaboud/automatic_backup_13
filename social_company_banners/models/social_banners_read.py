from odoo import models, fields, api
import logging


_logger = logging.getLogger(__name__)

class social_banner_read(models.Model):
    _name = 'social.banner.read'

    banner_id = fields.Many2one('social.banner', string="Banner")
    user_id = fields.Many2one('res.users', string="User")
    date = fields.Datetime(string="Read date")
