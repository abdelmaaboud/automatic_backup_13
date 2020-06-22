# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)

class ProjectTask(models.Model):
    _inherit = ['project.task']

    partner_phone = fields.Char(string="Partner phone", related='partner_id.phone')
    customer_feedback = fields.Text('Customer Feedback')
    planned_hours = fields.Float(track_visibility="onchange")
    
    @api.multi
    def write(self, vals):
        # Check if the selected stage need an assignation
        if 'stage_id' in vals and vals['stage_id'] and not self.user_id and 'user_id' not in vals:
            stage_id = self.env['project.task.type'].browse(vals['stage_id'])
            if stage_id.need_user_assignation:
                raise ValidationError(_("No one is assigned to this task, please assign someone."))
        
        return super(ProjectTask, self).write(vals)

    @api.multi
    def set_first_message_as_description(self):
        for task in self:
            if not task.description:
                # get the first message of the issue creator
                messages = task.message_ids.filtered(lambda r: r.author_id == task.partner_id).sorted(key=lambda r: r.date)
                if len(messages) > 0:
                    task.description = messages[0].body

    @api.multi
    def add_partner_as_task_follower(self):
        for task in self:
            if task.partner_id:
                follower_id = False
                for f in task.message_follower_ids:
                    if f.partner_id == task.partner_id:
                        follower_id = f
                        break
                if not follower_id:
                    follower_id = self.env['mail.followers'].create({
                        'res_id': task.id,
                        'res_model': 'project.task',
                        'partner_id': task.partner_id.id,
                    })
                follower_id.write({'subtype_ids':[[4, self.env.ref('mail.mt_comment').id, False]]})
                follower_id.write({'subtype_ids':[[4, self.env.ref('project.mt_task_stage').id, False]]})

    @api.multi
    def match_task_to_project(self):
        generic_email_suffixes = ['gmail.com', 'hotmail.com', 'hotmail.be', 'skynet.be', 'live.com', 'hotmail.fr', 'yahoo.com', 'yahoo.fr']

        for task in self:
            if not task.email_from:
                task.message_post(body="No email or partner on this task, impossible to match it automatically on a project")
                continue
            if not task.partner_id:
                task.message_post(body="No partner on this task, impossible to match it automatically on a project")
                continue

            email_match = False
            email_match_email = ''
            email_match_partner_id = None
            is_project_found = False

            # Get the suffix of the sender email address
            email_suffix = self.remove_email_special_chars(task.email_from.split("@")[1].lower())
            email_simple = self.remove_email_special_chars(task.email_from.lower())

            # We only match on Open/Pending Projects that are not installation, consulting or other
            project_ids = self.env['project.project'].search([
                ('state', 'in', ['open', 'pending']),
                ('project_type', 'in', ['support', 'development']),
                ('accept_email_from_support', '=', True)
            ])
            for project in project_ids:
                project_emails = []
                if project.analytic_account_id.partner_id:
                    # if (project.analytic_account_id.first_subscription_id or (project.analytic_account_id.first_subscription_id and project.analytic_account_id.first_subscription_id.state == 'open')) and project.analytic_account_id.partner_id and 'bl' in project.analytic_account_id.name.lower():

                    for partner in project.analytic_account_id.partner_id.child_ids:
                        if partner.email:
                            project_emails.append([partner.email.lower(), partner.id])
                    if project.analytic_account_id.partner_id.email:
                        project_emails.append([project.analytic_account_id.partner_id.email.lower(), project.analytic_account_id.partner_id.id])

                # Try to find the partner using its email from our contacts
                for email in project_emails:
                    if email[0] in email_simple:
                        email_match = True
                        email_match_email = email[0]
                        email_match_partner_id = email[1]

                # Contact not found, try to match on email suffixes
                if not email_match and (not email_suffix in generic_email_suffixes):
                    for email in project_emails:
                        if (email[0].find(email_suffix) > 0):
                            email_match = True
                            email_match_email = task.email_from
                            email_match_partner_id = task.partner_id.id

                if email_match:
                    task.write({
                        'project_id' : project.id,
                        'email_from' : email_match_email,
                        'partner_id' : email_match_partner_id,
                        'priority' : '1'
                    })

                    # Print a message in the description
                    if email_match_partner_id == None:
                        task.message_post(body="WARNING ! THIS SENDER HAS NO CONTACT LINKED, CREATE ONE PLEASE\nEMAIL: %s" % (email_match_email))

                    is_project_found = True

                if is_project_found:
                    break
            if not is_project_found:
                task.message_post(body="No project found")

    @api.multi
    def send_confirmation_email_to_customer(self):
        email_template_id = self.env.ref('project_tasks_integration.email_template_task_email_matching_answer')
        if email_template_id:
            email_template_id.sudo().send_mail(self.ids[0], force_send=True)

    @api.multi
    def send_alert_to_team(self):
        email_template_id = self.env.ref('project_tasks_integration.email_template_new_task_email_to_SM')[0]
        for task in self:
            if task.project_id.sale_subscription_id and task.project_id.sale_subscription_id.contract_team:
                email_list = ''
                for pid in task.project_id.sale_subscription_id.contract_team.users:
                    email_list += pid.partner_id.email + ';'
                email_template_id.sudo().send_mail(self.ids[0], force_send=True, email_values={'email_to': email_list})

    def remove_email_special_chars(self, email):
        email = email.replace('&#60;', '') # lower than
        email = email.replace('<', '') # lower than
        email = email.replace('&#62;', '') # greater than
        email = email.replace('>', '') # greater than
        return email

    # @api.multi
    # def write(self, values):
    #     if 'stage_id' in values and values.get('stage_id').need_estimate and values.get('planned_hours'):
    #
    #     return super(ProjectTask, self).write(values)

    @api.constrains('stage_id')
    def check_estimate_for_stage(self):
        for record in self:
            if record.planned_hours == 0.0 and record.stage_id.need_estimate and record.project_id.project_type == 'development' and record.master_type_id.need_estimate:
                raise Warning(_("Please estimate the time on the task moving to this stage."))

