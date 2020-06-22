# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class AccountAsset(models.Model):
    _inherit = 'account.asset.asset'
    
    @api.multi
    def _entry_count(self):
        super(AccountAsset, self)._entry_count()
        for asset in self:
            res = self.env['account.move'].search_count([('asset_id', '=', asset.id)])
            asset.entry_count = res or 0

    @api.multi
    def open_entries(self):
        res = super(AccountAsset, self).open_entries()
        
        asset_ids = []
        for asset in self:
            asset_ids.append(asset.id)
        return {
            'name': _('Journal Entries'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('asset_id', 'in', asset_ids)],
        }
