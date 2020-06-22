# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)


class AccountPaymentLineCreate(models.TransientModel):
    _inherit = 'account.payment.line.create'

    account_ids = fields.Many2many('account.account')
    due_date = fields.Date(default=lambda self: datetime.today())

    @api.model
    def default_get(self, field_list):
        res = super(AccountPaymentLineCreate, self).default_get(field_list)
        context = self.env.context
        assert context.get('active_model') == 'account.payment.order', \
            'active_model should be payment.order'
        assert context.get('active_id'), 'Missing active_id in context !'
        order = self.env['account.payment.order'].browse(context['active_id'])
        mode = order.payment_mode_id
        res.update({
            'account_ids': mode.default_account_ids.ids or False,
        })
        return res

    @api.onchange('account_ids')
    def change_account_ids(self):
        return self.move_line_filters_change()

    @api.multi
    def _prepare_move_line_domain(self):
        self.ensure_one()
        domain = [('reconciled', '=', False),
                  ('company_id', '=', self.order_id.company_id.id)]
        if self.journal_ids:
            domain += [('journal_id', 'in', self.journal_ids.ids)]
        if self.partner_ids:
            domain += [('partner_id', 'in', self.partner_ids.ids)]
        if self.target_move == 'posted':
            domain += [('move_id.state', '=', 'posted')]
        if not self.allow_blocked:
            domain += [('blocked', '!=', True)]
        if self.date_type == 'due':
            domain += [
                '|',
                ('date_maturity', '<=', self.due_date),
                ('date_maturity', '=', False)]
        elif self.date_type == 'move':
            domain.append(('date', '<=', self.move_date))
        if self.invoice:
            domain.append(('invoice_id', '!=', False))
        if self.payment_mode:
            if self.payment_mode == 'same':
                domain.append(
                    ('payment_mode_id', '=', self.order_id.payment_mode_id.id))
            elif self.payment_mode == 'same_or_null':
                domain += [
                    '|',
                    ('payment_mode_id', '=', False),
                    ('payment_mode_id', '=', self.order_id.payment_mode_id.id)]

        
        domain += [('account_id.internal_type', 'in', ['receivable', 'payable'])]
        # Exclude lines that are already in a non-cancelled
        # and non-uploaded payment order; lines that are in a
        # uploaded payment order are proposed if they are not reconciled,
        paylines = self.env['account.payment.line'].search([
            ('state', 'in', ('draft', 'open', 'generated')),
            ('move_line_id', '!=', False)])
        if paylines:
            move_lines_ids = [payline.move_line_id.id for payline in paylines]
            domain += [('id', 'not in', move_lines_ids)]
        if self.account_ids:
            domain += [('account_id', 'in', self.account_ids.ids)]
        return domain