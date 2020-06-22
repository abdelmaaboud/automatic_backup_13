# -*- coding: utf-8 -*-
# (c) 2018 AbAKUS IT SOLUTIONS

import logging
from odoo import api, fields, models, _
_logger = logging.getLogger(__name__)


class AccountAssetAssetForFinancialReport(models.Model):
    _inherit = "account.asset.asset"

    @api.multi
    def get_model_id_and_name(self):
        """
        Function jump to asset view from the drop down menu
        """
        return ['account.asset.asset', self.id, _('View Asset'), False]
