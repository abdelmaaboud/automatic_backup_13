# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class HrEmployeeWithOnboardingOutboardingProjects(models.Model):
    _inherit = 'hr.employee'

    onboarding_project_id = fields.Many2one('project.project', string='Onboarding Project')
    outboarding_project_id = fields.Many2one('project.project', string='Onboarding Project')

    @api.multi
    def action_create_onboarding_project(self):
        for employee in self:
            onboarding_project_template = self.env['hr.project.on.out.boarding'].search([('type', '=', 'onboarding')])
            if len(onboarding_project_template) == 0:
                raise ValidationError(_('No OnBoarding project defined! - There is no On-Boarding project defined in your system.'))

            if len(onboarding_project_template) > 1:
                onboarding_project_template = onboarding_project_template[0]

            project_id = self.env['project.project'].create({
                'name': "Onboarding: " + self.name + " : " + onboarding_project_template.name,
                'onboarding_project': True,
                'outboarding_project': False,
                'on_out_boarding_employee_id': employee.id,
            })
            # Add tasks
            for task in onboarding_project_template.project_id.task_ids:
                new_task_id = self.env['project.task'].create({
                    'name': task.name,
                    'project_id': project_id.id,
                })
            self.onboarding_project_id = project_id

    @api.multi
    def action_create_outboarding_project(self):
        for employee in self:
            outboarding_project_template = self.env['hr.project.on.out.boarding'].search([('type', '=', 'outboarding')])
            if len(outboarding_project_template) == 0:
                raise ValidationError(_('No OutBoarding project defined! - There is no Out-Boarding project defined in your system.'))

            if len(outboarding_project_template) > 1:
                outboarding_project_template = outboarding_project_template[0]

            project_id = self.env['project.project'].create({
                'name': "Outboarding: " + self.name + " : " + outboarding_project_template.name,
                'onboarding_project': False,
                'outboarding_project': True,
                'on_out_boarding_employee_id': employee.id,
            })
            # Add tasks
            for task in outboarding_project_template.project_id.task_ids:
                new_task_id = self.env['project.task'].create({
                    'name': task.name,
                    'project_id': project_id.id,
                })
            self.outboarding_project_id = project_id
