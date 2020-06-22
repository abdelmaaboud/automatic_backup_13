# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, tools, _
from datetime import datetime
from hashlib import md5
from odoo.tools.misc import formatLang
import time
from odoo.tools.safe_eval import safe_eval
from odoo.tools import append_content_to_html, DEFAULT_SERVER_DATE_FORMAT
import math

import logging

_logger = logging.getLogger(__name__)


class AccountFollowupReport(models.AbstractModel):
    _inherit = "account.followup.report"

    def get_lines(self, options, line_id=None):
        today = datetime.today().strftime('%Y-%m-%d')
        lines = super(AccountFollowupReport, self).get_lines(options, line_id)
        total = 0
        total_issued = 0
        total_interest = 0
        compute_allowance = False
        i = 0
        for line in lines:
            if 'type' in line:
                
                i += 1
                columns = line.get('columns', False)
                if columns:
                    aml = self.env['account.move.line'].browse(line.get('id'))
                    columns.pop(2)
                    communication = '/'
                    if aml.invoice_id:
                        if aml.invoice_id.origin:
                            communication =  aml.invoice_id.origin
                        elif aml.invoice_id.name:
                            communication =  aml.invoice_id.name
                    elif aml.name:
                        communication = aml.name
                    columns.insert(2, {'name': communication})
                    # Late days
                    late_days = aml.late_days > 0 and aml.late_days or 0
                    columns.insert(2, {'name': late_days})
                    #followup level
                    followup = self.env['account_followup.followup'].search([('company_id', '=', aml.company_id.id)])
                    followup_line_id = followup.followup_line_ids.sorted('delay')[0]
                    if aml.followup_line_id:
                        next = False
                        for fupl in followup.followup_line_ids.sorted('delay'):
                            if next == True:
                                followup_line_id = fupl
                                next = False
                            if fupl.id == aml.followup_line_id.id:
                                next = True
                        
                    if followup_line_id:
                        level = followup_line_id.sequence
                    else:
                        level = "0"
                    columns.insert(3, {'name': level})
                    
                    # Remove expected date
                    if not self.env.context.get('print_mode'):
                        columns.pop(5)

                    # allowances/interests/total
                    amount = aml.currency_id and aml.amount_residual_currency or aml.amount_residual
#                     allowances = formatLang(self.env, aml.payments_allowances, currency_obj=aml.currency_id)
                    currency = aml.currency_id or (aml.partner_id and aml.partner_id.currency_id) or (aml.company_id and aml.company_id.currency_id)
                    interests = formatLang(self.env, aml.payments_interests, currency_obj=currency)
                    total_due = formatLang(self.env, float(amount + aml.payments_interests),
                                           currency_obj=currency)
        
#                     if aml.currency_id:
#                         interests = aml.currency_id.amount_to_text(aml.payments_interests)

                    columns += [{'name': interests}, {'name': total_due}]

                    # compute totals
                    total += not aml.blocked and amount or 0
                    total_interest += not aml.blocked and aml.payments_interests or 0
                    if not compute_allowance:
                        compute_allowance = not aml.blocked and aml.payments_allowances
                    is_overdue = today > aml.date_maturity if aml.date_maturity else today > aml.date
                    is_payment = aml.payment_id
                    if is_overdue or is_payment:
                        total_issued += not aml.blocked and amount or 0
                    
                    # update columns
                    line['columns'] = columns
        lines = lines[:i]
        number_of_columns = (6 if self.env.context.get('print_mode') else 7)
        total_allowance = compute_allowance or 0
        total_all = total_issued + total_interest + total_allowance
        total_str = formatLang(self.env, total, currency_obj=aml.currency_id)
        lines.append({
            'id': i,
            'name': '',
            'class': 'total',
            'unfoldable': False,
            'level': 0,
            'columns': [{'name': v} for v in
                        [''] * number_of_columns + [total >= 0 and _('Total Due') or '',
                                                                                   total_str]],
        })
        if total_issued > 0:
            total_issued = formatLang(self.env, total_issued, currency_obj=aml.currency_id)
            i += 1
            lines.append({
                'id': i,
                'name': '',
                'class': 'total',
                'unfoldable': False,
                'level': 0,
                'columns': [{'name': v} for v in
                            [''] * number_of_columns + [_('Total Overdue'),
                                                                                       total_issued]],
            })
        if total_allowance > 0:
            total_allowance = formatLang(self.env, total_allowance, currency_obj=aml.currency_id)
            i += 1
            lines.append({
                'id': i,
                'name': '',
                'class': 'total',
                'unfoldable': False,
                'level': 0,
                'columns': [{'name': v} for v in
                            [''] * number_of_columns + [_('Total Allowances'),
                                                                                       total_allowance]],
            })
        if total_interest > 0:
            total_interest = formatLang(self.env, total_interest, currency_obj=aml.currency_id)
            i += 1
            lines.append({
                'id': i,
                'name': '',
                'class': 'total',
                'unfoldable': False,
                'level': 0,
                'columns': [{'name': v} for v in
                            [''] * number_of_columns + [_('Total Interrests'),
                                                                                       total_interest]],
            })

        total_all = formatLang(self.env, total_all, currency_obj=aml.currency_id)
        i += 1
        lines.append({
            'id': i,
            'name': '',
            'class': 'total',
            'unfoldable': False,
            'level': 0,
            'columns': [{'name': v} for v in
                        [''] * number_of_columns + [_('Total'), total_all]],
        })
        return lines

    def get_columns_name(self, options):
        names = [
            {'name': _('Document')},
            {'name': _('Date'), 'class': 'date', 'style': 'text-align:center; white-space:nowrap;'},
            {'name': _('Due Date'), 'class': 'date', 'style': 'text-align:center; white-space:nowrap;'},
            {'name': _('Overdue days'), 'class': 'number', 'style': 'text-align:center; white-space:nowrap;'},
            {'name': _('Followup Level'), 'class': 'number', 'style': 'text-align:center; white-space:nowrap;'},
            {'name': _('Communication'), 'class': 'number', 'style': 'text-align:left; white-space:nowrap;'},
            {'name': _('Amount'), 'class': 'number', 'style': 'white-space:nowrap;'},
            {'name': _('Interests'), 'class': 'number', 'style': 'white-space:nowrap;'},
            {'name': _('Total Due'), 'class': 'number', 'style': 'white-space:nowrap;'},
        ]
        if not self.env.context.get('print_mode'):
            names.insert(6, {'name': _('Excluded'), 'class': 'number', 'style': 'text-align:center; white-space:nowrap;'},)
        return names
    

# class account_report_context_followup(models.TransientModel):
#     _inherit = "account.report.context.followup"
#
#
#     @api.multi
#     def get_columns_types(self):
#         if self.env.context.get('public'):
#             return ['date', 'date', 'number', 'number', 'number', 'number', 'number']
#         return ['date', 'date', 'number', 'date', 'checkbox', 'number', 'number', 'number', 'number']
