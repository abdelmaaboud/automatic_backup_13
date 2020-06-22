# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, tools, _
from datetime import datetime
from hashlib import md5
from odoo.tools.misc import formatLang
import time
from odoo.tools.safe_eval import safe_eval
from odoo.tools import append_content_to_html, DEFAULT_SERVER_DATE_FORMAT
import math

import logging

_logger = logging.getLogger(__name__)


class AccountAgedPartner(models.AbstractModel):
    _inherit = "account.aged.partner"

    def get_columns_name(self, options):
        names = super(AccountAgedPartner, self).get_columns_name(options)
        names.insert(1, {'name': "Followup Level"})
        return names

    def get_lines(self, options, line_id=None):
        lines = super(AccountAgedPartner, self).get_lines(options, line_id)
        for line in lines:
            name = ''
            if 'parent_id' in line and ('class' not in line or 'o_account_reports_domain_total' not in line['class']):
                aml = self.env['account.move.line'].browse(line['id'])
                name = aml.followup_line_id.sequence if aml and aml.followup_line_id and aml.followup_line_id.sequence else 0
            columns = line['columns']
            columns = [{'name': name}] + columns
            line['columns'] = columns
        return lines
