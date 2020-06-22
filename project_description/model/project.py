from odoo import models, fields

class ProjectProject(models.Model):
    _inherit = ['project.project']

    project_description = fields.Text(string="Description")
