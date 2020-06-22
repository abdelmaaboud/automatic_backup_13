# -*- coding: utf-8 -*-
from odoo import fields, models, api
import logging

_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = 'res.company'

    portal_help_home = fields.Text(string="Home help", translate="True")
    portal_help_expense_list_view = fields.Text(string="Expense list view help", translate="True")
    portal_help_expense_form_view = fields.Text(string="Expense form view help", translate="True")
    portal_help_leave_list_view = fields.Text(string="Leave list view help", translate="True")
    portal_help_leave_form_view = fields.Text(string="Leave form view help", translate="True")
    portal_help_timesheet_list_view = fields.Text(string="Timesheet list view help", translate="True")
    portal_help_timesheet_form_view = fields.Text(string="Timesheet form view help", translate="True")
