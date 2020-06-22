# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class account_next_sequence(models.Model):
    _inherit = ['account.bank.statement']
    bank_account_balance = fields.Float(compute='_compute_bank_account_balance', string="Bank account balance")
    
    @api.depends('journal_id')
    def _compute_bank_account_balance(self):
        if self.journal_id:
            self.bank_account_balance = self.journal_id.default_debit_account_id.compute_account_balance()
        else:
            self.bank_account_balance = -1

class account_with_balance(models.Model):
    _inherit = ['account.account']

    @api.multi
    def compute_account_balance(self):
        move_ids = self.env['account.move.line'].search([('account_id', '=', self.id)])
        debit = 0
        credit = 0
        for move in move_ids:
            debit += move.debit
            credit += move.credit
        balance = debit - credit
        return balance
