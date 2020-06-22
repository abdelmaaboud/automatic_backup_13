# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


import logging
_logger = logging.getLogger(__name__)

class project_task_service_desk(models.Model):
    _inherit = ['project.task']

    project_type = fields.Selection(related='project_id.project_type', string='Project Type', store=True)
    user_id = fields.Many2one(default=lambda self: self.env.uid if self.env['res.users'].browse(self.env.uid).automatically_assign_to_created_task else None)
    
    def _get_default_stage_id(self):
        """ Gives default stage_id """
        project_id = self.env.context.get('default_project_id')
        if project_id:
            return self.stage_find(project_id, [('fold', '=', False)])
        analytic_account_id = self.env.context.get('default_analytic_account_id')
        if analytic_account_id:
            project_id = self.env['project.project'].search([('analytic_account_id', '=', self.env.context.get('default_analytic_account_id'))])
            if project_id:
                return self.stage_find(project_id, [('fold', '=', False)])

        return False

    @api.model
    def create(self, vals):
        context = dict(self.env.context, mail_create_nolog=True)
        if not vals.get('user_id') and context.get('default_user_id'):
            user_id = self.env['res.users'].browse(context.get('default_user_id'))
            if user_id.automatically_assign_to_created_task:
                vals['user_id'] = context.get('default_user_id')
        task = super(project_task_service_desk, self.with_context(context)).create(vals)
        return task
