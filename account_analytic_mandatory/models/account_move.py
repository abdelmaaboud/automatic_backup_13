# -*- coding: utf-8 -*-
# (c) 2018 - AbAKUS IT SOLUTIONS

import logging
from pprint import pformat
from odoo import models, api, fields, _
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def _post_validate(self):
        """ We override this method in order to check if an analytic account is required """
        for move in self:
            if move.line_ids:
                for line in move.line_ids:
                    if line.account_id and line.account_id.is_analytic_mandatory and not line.analytic_account_id:
                        msg = "Please define an analytic account before posting to this account: [{} {}]"
                        raise UserError(_(msg).format(line.account_id.code, line.account_id.name))
        return super(AccountMove, self)._post_validate()
