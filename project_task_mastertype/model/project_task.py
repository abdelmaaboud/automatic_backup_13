# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
import logging
_logger = logging.getLogger(__name__)

class ProjectTask(models.Model):
    _inherit = ['project.task']

    def _get_default_master_type(self):
        if self.env.context:
            if self.env.context.get('master_type_id'):
                return self.env.context.get('master_type_id')
            if self.env.context.get('default_project_id'):
                project_id = self.env['project.project'].browse([self.env.context.get('default_project_id')])
                if project_id.default_task_master_type_id:
                    return project_id.default_task_master_type_id
            if self.env.context.get('project_id'):
                project_id = self.env['project.project'].browse([self.env.context.get('project_id')])
                if project_id.default_task_master_type_id:
                    return project_id.default_task_master_type_id
        return self.env.ref('project_task_mastertype.task', False) and self.env.ref('project_task_mastertype.task') or self.env['project.task.mastertype']

    possible_types = fields.Many2many(related='project_id.possible_task_master_type_ids')
    master_type_id = fields.Many2one('project.task.mastertype', domain="[('id', 'in', possible_types)]" ,string="Task type", track_visibility="onchange", required=True, default=_get_default_master_type)
    master_type_code = fields.Char(related='master_type_id.code', string="Type code")

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            if record.master_type_id:
                result.append((record.id, "[%s] %s" % (record.master_type_code, record.name)))
            else:
                result.append((record.id, "%s" % (record.name)))
        return result

    @api.multi
    def project_changed(self):
        for task in self:
            if task.project_id:
                task.master_type_id = task.project_id.default_task_master_type_id
