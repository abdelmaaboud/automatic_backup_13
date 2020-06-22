# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _

import logging
_logger = logging.getLogger(__name__)
    
    
class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    close_stage = fields.Boolean(string="Selected Close Stage", default=False)
    
    # def _reset_other_close_stage(self):
    #     types = self.env['project.task.type'].search([('id', '!=', self.id), ('close_stage', '=', True)])
    #
    #     for t in types:
    #         t.close_stage = False
    #
    # @api.model
    # def create(self, values):
    #     if values.get('close_stage'):
    #         self._reset_other_close_stage()
    #
    #     return super(ProjectTaskType, self).create(values)
    #
    # @api.one
    # def write(self, values):
    #     if values.get('close_stage'):
    #         self._reset_other_close_stage()
    #
    #     return super(ProjectTaskType, self).write(values)
