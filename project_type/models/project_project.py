# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
import logging
_logger = logging.getLogger(__name__)

class ProjectProject(models.Model):
    _inherit = ['project.project']


    def _get_default_project_type(self):
        context = self.env.context
        if context is None:
            context = {}
        if 'default_project_type' in context:
            if context['default_project_type']:
                return context['default_project_type']
        return False

    project_type = fields.Selection([
        ('support', 'Support'),
        ('installation', 'Installation'),
        ('internal', 'Internal'),
        ('development', 'Development'),
        ('consulting', 'Consulting'),
        ('other', 'Other')],
        'Type of Project', default=_get_default_project_type)
