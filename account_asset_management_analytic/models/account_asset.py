# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'

    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic account')

    @api.onchange('category_id')
    def onchange_category_id(self):
        if self.category_id and self.category_id.account_analytic_id:
            self.account_analytic_id = self.category_id.account_analytic_id


class AccountAssetDepreciationLine(models.Model):
    _inherit = 'account.asset.depreciation.line'

    @api.multi
    def create_move(self, post_move=True):
        created_move_ids = super(AccountAssetDepreciationLine, self).create_move(post_move)
        for move in self.env['account.move'].browse(created_move_ids):
            for move_line in move.line_ids:
                # Set the AA
                if move_line.debit > 0 and move.asset_id.account_analytic_id:
                    move_line.analytic_account_id = move.asset_id.account_analytic_id
                    # Create an AAL
                    aal_id = self.env['account.analytic.line'].create({
                        'name': move_line.name,
                        'user_id': self.env.uid,
                        'account_id': move.asset_id.account_analytic_id.id,
                        'partner_id': move.partner_id.id,
                        'date': move.date,
                        'amount': move_line.debit,
                        'unit_amount': 1,
                        'move_id': move_line.id,
                    })
        return created_move_ids
