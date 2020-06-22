# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions SARL
# in Luxembourg 2019

from odoo import models, fields, api, _

class ProjectTask(models.Model):
    _inherit = ['project.task']

    warning_text = fields.Text(string="Warning Text", related='project_id.warning_text', readonly=True)
