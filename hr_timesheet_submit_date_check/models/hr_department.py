# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class HrDepartment(models.Model):
    _inherit = ['hr.department']

    timesheet_submission_date_check = fields.Boolean(string="Check timesheet submission date")
    default_timesheet_duration = fields.Selection([('week', 'Weekly'), ('month', 'Monthly'), ('year', 'Yearly')], string="Timesheet default period")
    timesheet_submission_date_delay_days = fields.Integer(string="Day(s) between end of the TS and submission")
    timesheet_submission_date_delay_hour = fields.Integer(string="Hour of the day after delay of the TS and submission (0-23)")
