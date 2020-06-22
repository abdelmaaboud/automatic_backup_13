# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    asset_id = fields.Many2one('account.asset.asset', string='Asset')
    
    @api.model
    def create(self, vals):
        move = super(AccountMove, self.with_context(check_move_validity=False, partner_id=vals.get('partner_id'))).create(vals)
        if move.asset_id:
            move.create_depreciation_line()
        return move
    
    def create_depreciation_line(self):
        depreciated_value = self._compute_depreciated_value()
        remaining_value = self.asset_id.value - depreciated_value
        sequence = len(self.asset_id.depreciation_line_ids) + 1
        vals = {
            'name': (self.asset_id.code or '') + '/' + str(sequence),
            'asset_id': self.asset_id.id,
            'sequence': sequence,
            'move_id': self.id,
            'move_check': True,
            'amount': self.amount,
            'depreciation_date': self.date,
            'depreciated_value': depreciated_value,
            'remaining_value': remaining_value
        }
        self.env['account.asset.depreciation.line'].create(vals)
        
    def _compute_depreciated_value(self):
        total = 0.0
        for depreciation_line in self.asset_id.depreciation_line_ids:
            total += depreciation_line.amount
            
        return total
