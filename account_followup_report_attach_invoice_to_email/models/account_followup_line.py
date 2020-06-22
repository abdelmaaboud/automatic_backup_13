# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools import append_content_to_html

import base64
import logging
_logger = logging.getLogger(__name__)


class AccountFollowupLine(models.Model):
    _inherit = 'account_followup.followup.line'

    subject = fields.Char("Mail Subject", translate=True)
    signature = fields.Char("Mail Signature", translate=True)
    description_bottom = fields.Text('Bottom Printed Message', translate=True)
