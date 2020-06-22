# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools import float_compare
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = "account.move"

    @api.multi
    def reconcile(self, writeoff_acc_id=False, writeoff_journal_id=False):
        res = super(AccountMove, self).reconcile(writeoff_acc_id=writeoff_acc_id, writeoff_journal_id=writeoff_journal_id)
        account_move_ids = [l.move_id.id for l in self if float_compare(l.move_id.matched_percentage, 1, precision_digits=5) == 0]
        if account_move_ids:
            expense_sheets = self.env['hr.expense.sheet'].search([
                ('account_move_id', 'in', account_move_ids), ('state', '!=', 'done')
            ])
            expense_sheets.set_to_paid()
        return res

    @api.multi
    def post(self):
        res = super(AccountMove, self).post()

        for move in self:
            expense_sheets = self.env['hr.expense.sheet'].search([
                ('account_move_id', 'in', [move.id]), ('state', '!=', 'done')
            ])
            if len(expense_sheets) > 0:
                expense_sheets.write({'state': 'post'})

