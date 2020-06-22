# -*- coding: utf-8 -*-
from odoo import models, api, _

import logging

_logger = logging.getLogger(__name__)


class HrHolidays(models.Model):
    _inherit = 'hr.holidays'

    @api.multi
    def name_get(self):
        result = []
        for holiday in self:
            if holiday.type == "remove":
                result.append((holiday.id, _("%s - %s (%s -> %s)") % (holiday.employee_id.name, holiday.name, holiday.date_from, holiday.date_to)))
            else:
                result.append((holiday.id, holiday.name))
        return result
