# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
from odoo import api, models, fields
import math

class HrHolidayArchived(models.Model):
    _inherit = 'hr.holidays'

    active = fields.Boolean(default=True)

    @api.model
    def _archive_holiday(self):
        for holiday in self:
            if holiday.active:
                holiday.active = False
            else:
                holiday.active = True
