# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
import logging
from datetime import datetime, timedelta
import pytz
import time
import math
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT,DEFAULT_SERVER_DATETIME_FORMAT
_logger = logging.getLogger(__name__)

class HrTimesheetSheet(models.Model):
    _inherit = 'hr_timesheet.sheet'

    leave_ids = fields.Many2many('hr.holidays', compute="compute_leaves")

    @api.depends('date_start', 'date_end', 'employee_id')
    def compute_leaves(self):
        for sheet in self:
            sheet.leave_ids = self.env['hr.holidays'].search([('date_from', '<', sheet.date_end), ('date_to', '>', sheet.date_start), ('state', '=', 'validate'), ('employee_id', '=', sheet.employee_id.id)])