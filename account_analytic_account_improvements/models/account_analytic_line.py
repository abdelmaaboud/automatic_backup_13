# -*- coding: utf-8 -*-

from odoo import models, fields, api

import logging
_logger = logging.getLogger(__name__)

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    @api.model
    def _get_default_to_invoice(self):
        return self.env.ref('account_analytic_account_improvements.hr_timesheet_invoice_factor_100', False) and self.env.ref('account_analytic_account_improvements.hr_timesheet_invoice_factor_100') or self.env['hr_timesheet_invoice.factor']

    invoice_id = fields.Many2one('account.invoice', string='Invoice')
    to_invoice = fields.Many2one('hr_timesheet_invoice.factor', string='Invoiceable', default=lambda self: self._get_default_to_invoice())
    invoicable_unit_amount = fields.Float(string="Invoicable Quantity")
    is_outside_resource_calendar = fields.Boolean(string="Outside Resource Calendar")
    manual_settings = fields.Boolean(string="Set info manually", default=False)

    @api.model
    def create(self, vals, context=None):
        # Set the invoicable unit amount the same as the real amount * the min set in the contract
        if 'unit_amount' in vals:
            amount = vals['unit_amount']
            # Check if there is a min invoicable amount on the subscription
            subscription_id = False
            if 'account_id' in vals:
                subscription_id = self.env['sale.subscription'].search([('analytic_account_id', '=', vals['account_id'])])
            elif 'project_id' in vals:
                project_id = self.env['project.project'].search([('id', '=', vals['project_id'])])
                subscription_id = self.env['sale.subscription'].search([('analytic_account_id', '=', project_id.analytic_account_id.id)])
            if subscription_id:
                # If amount is less than the minimum on the subs, replace by the minimum
                amount = subscription_id.minimum_invoicable_quantity if subscription_id.minimum_invoicable_quantity > amount else amount
            vals.update({
                'invoicable_unit_amount': amount,
            })

        return super(AccountAnalyticLine, self).create(vals)

    @api.multi
    def write(self, values):
        if 'unit_amount' in values:
            amount = values['unit_amount']
            # Check if there is a min invoicable amount on the subscription
            subscription_id = self.env['sale.subscription'].search([('analytic_account_id', '=', self.account_id.id)])
            if subscription_id:
                # If amount is less than the minimum on the subs, replace by the minimum
                amount = subscription_id.minimum_invoicable_quantity if subscription_id.minimum_invoicable_quantity > amount else amount
            values.update({
                'invoicable_unit_amount': amount,
            })

        res = super(AccountAnalyticLine, self).write(values)
        return res
