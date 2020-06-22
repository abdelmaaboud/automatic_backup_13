# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
import time
import logging
_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = ['account.move.line']

    payments_interests = fields.Float(compute="_compute_payments_interests", string="Due interests")
    payments_allowances = fields.Float(compute="_compute_payments_allowances", string="Due allowances")
    late_days = fields.Integer(compute="_compute_late_days", string="Late Days")

    @api.multi
    def _compute_late_days(self):
        for line in self:
            d1 = datetime.strptime(line.date_maturity, '%Y-%m-%d')
            d2 = datetime.strptime(time.strftime('%Y-%m-%d'), '%Y-%m-%d')
            daysDiff = float(str((d2-d1).days))
            line.late_days = daysDiff

    @api.multi
    def _compute_payments_interests(self):
        followup = self.env['account_followup.followup'].search([['company_id', '=', self.env.user.company_id.id]])
        if len(followup) <= 0:
            return
        if len(followup) > 1:
            followup = followup[0]

        for line in self:
            # set to zero
            line.payments_interests = 0

            # check if date exceeded and we have to compute interests
            check = False
            if line.followup_line_id and line.followup_line_id.compute_interests:
                check = True
            # check if date is overpassed AND level was already set (means that we did an action)

            for f_line in followup.followup_line_ids:
                if f_line.delay < line.late_days and f_line.compute_interests:
                    check = True

            amount = line.currency_id and line.amount_residual_currency or line.amount_residual
            if check and not line.full_reconcile_id and not line.blocked and line.date_maturity and amount > 0.0:
                balance = abs(line.debit - line.credit)
                if line.late_days > 0:
                    pc = float(followup.late_interest_percentage) / 100
                    pc_per_day = float(pc / 365)
                    interrests = float(balance * pc_per_day * line.late_days)
                    if interrests < 0:
                        interrests = interrests * (-1)
                    line.payments_interests = interrests
                    line.write({'payments_interests': interrests})

    @api.multi
    def _compute_payments_allowances(self):
        followup = self.env['account_followup.followup'].search([['company_id', '=', self.env.user.company_id.id]])
        if len(followup) <= 0:
            return
        if len(followup) > 1:
            followup = followup[0]

        for line in self:
            # set to zero
            line.payments_allowances = 0

            # check if line is set to a specific followup level
            check = False
            if line.followup_line_id and line.followup_line_id.compute_allowance:
                check = True
            # check if date is overpassed AND level was already set (means that we did an action)
            for f_line in followup.followup_line_ids:
                if f_line.delay < line.late_days and f_line.compute_allowance:
                    check = True

            amount = line.currency_id and line.amount_residual_currency or line.amount_residual
            if check and not line.full_reconcile_id and not line.blocked and amount > 0.0:
                line.write({'payments_allowances': followup.late_allowance})
                line.payments_allowances = followup.late_allowance

    @api.multi
    def get_model_id_and_name(self):
        """Function used to display the right action on journal items on dropdown lists, in reports like general ledger"""
        if self.statement_id:
            return ['account.bank.statement', self.statement_id.id, _('View Bank Statement'), False]
        if self.payment_id:
            return ['account.payment', self.payment_id.id, _('View Payment'), False]
        if self.invoice_id:
            view_id = self.invoice_id.get_formview_id()
            return ['account.invoice', self.invoice_id.id, _('View Invoice'), view_id]
        return ['account.move', self.move_id.id, _('View Move'), False]
