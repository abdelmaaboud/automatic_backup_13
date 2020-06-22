from odoo import models, fields

class AnalyticAccount(models.Model):
    _inherit = 'project.task'

    priority = fields.Selection(selection_add= [
                ('2', 'High'),
                ('3', 'Very High')
                ], track_visibility="onchange")