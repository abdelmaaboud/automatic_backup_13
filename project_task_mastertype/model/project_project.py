# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
import logging
_logger = logging.getLogger(__name__)

class ProjectProject(models.Model):
    _inherit = ['project.project']

    default_task_master_type_id = fields.Many2one('project.task.mastertype', string="Default Task Type", domain="[('id', 'in', possible_task_master_type_ids)]")
    possible_task_master_type_ids = fields.Many2many('project.task.mastertype', string="Possible Tasks Types", default=lambda self: self._get_master_types())
    
    @api.model
    def _get_master_types(self):
        return self.env['project.task.mastertype'].search([]).ids
        
    
    @api.multi
    @api.onchange('default_task_master_type_id')
    def change_task_name(self):
        for project in self:
            if project.default_task_master_type_id:
                project.label_tasks = project.default_task_master_type_id.name
