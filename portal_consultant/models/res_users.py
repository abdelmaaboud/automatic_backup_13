# -*- coding: utf-8 -*-
from odoo import fields, models, api
import logging

_logger = logging.getLogger(__name__)

class Users(models.Model):
    _inherit = 'res.users'

    is_consultant = fields.Boolean(string="Consultant", default=False)
    timesheet_current_project_project_id_related = fields.Many2one('project.project',
                                                                    string="Current Project Project ID",
                                                                    related='employee_ids.timesheet_current_project_project_id')


    timesheet_current_project_task_id_related = fields.Many2one('project.task', string="Current Working Task", related='employee_ids.timesheet_current_project_task_id')
    @api.multi
    def change_consultant_rights(self):
        for user in self:
            # Is internal, convert to consultant
            if not user.is_consultant:
                # Get all groups where the user is and remove it from there
                self.env['res.groups'].search([]).write({'users': [(3, user.id)]})

                # Add the user to the groups needed for portal
                self.env.ref('base.group_portal').write({'users': [(4, user.id)]})
                self.env.ref('base.group_no_one').write({'users': [(4, user.id)]})
                self.env.ref('sale.group_show_price_subtotal').write({'users': [(4, user.id)]})

                user.is_consultant = True

            # Is consultant, convert to internal
            else:
                # Add it to the internal group of employees
                self.env.ref('base.group_user').write({'users': [(4, user.id)]})

                user.is_consultant = False
