from odoo import models, fields

class AnalyticAccount(models.Model):
    _inherit = 'project.task'

    customer_feedback = fields.Text(string="Customer Feedback")
