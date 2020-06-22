# -*- coding: utf-8 -*-
from odoo import fields, models


class Project_Project(models.Model):
    _inherit = 'project.project'

    portal_selectable = fields.Boolean(string="Can be selected on portal for TS", default=False)
