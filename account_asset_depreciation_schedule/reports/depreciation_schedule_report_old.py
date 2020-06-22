# -*- coding: utf-8 -*-
# (c) 2018 - AbAKUS IT SOLUTIONS

import logging
from pprint import pformat
from odoo import models, api, fields, _
from odoo.tools.misc import formatLang
_logger = logging.getLogger(__name__)


class ReportAccountDepreciationSchedule(models.AbstractModel):
    _name = "account.depreciation.schedule"
    _description = "Depreciation Schedule Report"

    def _format(self, value, currency=False):
        if self.env.context.get('no_format'):
            return value
        currency_id = currency or self.env.user.company_id.currency_id
        if currency_id.is_zero(value):
            # don't print -0.0 in reports
            value = abs(value)
        res = formatLang(self.env, value, currency_obj=currency_id)
        return res

    @staticmethod
    def model_data(obj):
        fields_dict = {}
        for key in obj.fields_get():
            fields_dict[key] = obj[key]
        return fields_dict

    @api.model
    def get_title(self):
        return _("Depreciation Schedule")

    @api.model
    def get_report_type(self):
        """ modeled after general ledger """
        return 'no_comparison'

    @api.model
    def get_name(self):
        return 'depreciation_schedule'

    @api.model
    def get_template(self):
        return 'account_reports.report_financial'

    @api.model
    def get_lines(self, context_id, line_id=None):
        if type(context_id) == int:
            context_id = self.env['account.context.depreciation.schedule'].search([['id', '=', context_id]])
        new_context = dict(self.env.context)
        new_context.update({
            'date_from': context_id.date_from,
            'date_to': context_id.date_to,
            'state': context_id.all_entries and 'all' or 'posted',
            'cash_basis': context_id.cash_basis,
            'context_id': context_id,
            'company_ids': context_id.company_ids.ids,
        })
        return self.with_context(new_context)._lines(line_id)

    def _lines(self, context_id, line_id=None):
        """ Returns report lines. When line_id is passed we are unfolding to access a sub line """
        lines = []
        context = self.env.context
        company_id = context.get('company_id') or self.env.user.company_id
        # unfold_all = context.get('print_mode') and not context['context_id']['unfolded_categories']
        unfold_all = True
        # first group by categories
        category_obj = self.env['account.asset.category']
        category_ids = category_obj.search([('company_id', '=', company_id.id), ])
        cur_line = 0
        # Full addition:
        total_amount_from = total_amount_to = 0.0
        total_amount_plus = total_amount_minus = 0.0

        total_deprec_from = total_deprec_to = 0.0
        total_deprec_plus = total_deprec_minus = 0.0
        grand_total_line = []
        for cat in category_ids:
            # Do not display category twice
            cur_line += 1
            if line_id and line_id != cur_line:
                continue
            # Remove unwanted categories
            # NOTE: We keep closed assets.
            # NOTE: Wait until we confirm that correcting Journals doesn't break something else
            #       Then we will be able to filter on journal code and only keep
            #       cat.account_asset_id.code of type 2xxx000
            # Category line
            lines.append(
                {
                    'id': cat.id,
                    'type': 'line',
                    'name': cat.account_asset_id.code + " " +
                            cat.display_name + " (" +
                            context.get('date_from') + " to " +
                            context.get('date_to') + ")",
                    'footnotes': [],
                    'columns': [
                        "", "", "", "", "", "",
                        "", "", "", "", "", "",
                        "", "", "", ],
                    'level': 2,
                    'unfoldable': True,
                    'unfolded': unfold_all,
                    'colspan': 4,
                }
                # 'unfolded': cat in context['context_id']['unfolded_categories'] or unfold_all,
            )
            # Go deeper for each category
            # if cat in context['context_id']['unfolded_categories'] or unfold_all:
            if unfold_all:
                domain_lines = []
                asset_obj = self.env['account.asset.asset']
                # No filtering on dates here since we want all assets
                asset_ids = asset_obj.search([('company_id', '=', company_id.id),
                                              ('category_id', '=', cat.id),
                                              ], order='date')
                # Total lines
                total_asset_amount_from = 0.0
                total_asset_amount_to = 0.0
                total_asset_amount_plus = 0.0
                total_asset_amount_minus = 0.0

                total_asset_deprec_from = 0.0
                total_asset_deprec_to = 0.0
                total_asset_deprec_plus = 0.0
                total_asset_deprec_minus = 0.0
                for asset in asset_ids:
                    # Assets ==============
                    asset_amount_from = 0.0
                    asset_amount_to = 0.0
                    asset_amount_plus = 0.0
                    asset_amount_minus = 0.0

                    asset_deprec_from = 0.0
                    asset_deprec_to = 0.0
                    asset_deprec_plus = 0
                    asset_deprec_minus = 0

                    if asset.date <= context.get('date_from'):
                        asset_amount_from = asset.value
                    if asset.date <= context.get('date_to'):
                        asset_amount_to = asset.value

                    if asset_amount_from < asset_amount_to:
                        asset_amount_plus = asset_amount_to - asset_amount_from
                    else:
                        asset_amount_minus = asset_amount_from - asset_amount_to

                    total_asset_amount_from += asset_amount_from
                    total_asset_amount_to += asset_amount_to
                    total_asset_amount_plus += asset_amount_plus
                    total_asset_amount_minus += asset_amount_minus

                    # Depreciation ============
                    for idx, dl in enumerate(asset.depreciation_line_ids):
                        if idx == 0:
                            # This allow taking into account asset's initial depreciation value
                            # for assets acquired before registration in 0doo.
                            # Value would be 0 for assets fully created and managed in Odoo.
                            asset_deprec_from += dl.depreciated_value
                            asset_deprec_to += dl.depreciated_value
                        if dl.depreciation_date <= context.get('date_from'):
                            asset_deprec_from += dl.amount
                        if dl.depreciation_date <= context.get('date_to'):
                            asset_deprec_to += dl.amount

                    if asset_deprec_from < asset_deprec_to:
                        asset_deprec_plus = asset_deprec_to - asset_deprec_from
                    else:
                        asset_deprec_minus = asset_deprec_from - asset_deprec_to

                    total_asset_deprec_from += asset_deprec_from
                    total_asset_deprec_to += asset_deprec_to
                    total_asset_deprec_plus += asset_deprec_plus
                    total_asset_deprec_minus += asset_deprec_minus
                    # Build second level lines
                    progress_factor = 100
                    if asset.method_number > 0 and asset.method_period > 0:
                        progress_factor = 100 / ((asset.method_number * asset.method_period) / 12)
                    domain_lines.append(
                        {
                            'id': asset.id,
                            'type': 'account_asset_asset',
                            'action': asset.get_model_id_and_name(),
                            'name': "ASSET/{:04d}".format(asset.id),
                            'footnotes': [],
                            'columns': [
                                asset.code,
                                asset.display_name,
                                "L" if asset.category_id.method == _('linear') else "?",
                                progress_factor,
                                "M",
                                asset.date,
                                self._format(asset_amount_from), self._format(asset_amount_plus),
                                self._format(asset_amount_minus), self._format(asset_amount_to),
                                self._format(asset_deprec_from), self._format(asset_deprec_plus),
                                self._format(asset_deprec_minus), self._format(asset_deprec_to),
                                self._format(asset_amount_to - asset_deprec_to),
                            ],
                            'level': 1,
                        }
                    )

                domain_lines.append({
                    'id': cat.id,
                    'type': 'o_account_reports_domain_total',
                    'name': 'Total',
                    'footnotes': [],
                    'columns': ['', '', '', '', '', '',
                                self._format(total_asset_amount_from), self._format(total_asset_amount_plus),
                                self._format(total_asset_amount_minus), self._format(total_asset_amount_to),
                                self._format(total_asset_deprec_from), self._format(total_asset_deprec_plus),
                                self._format(total_asset_deprec_minus), self._format(total_asset_deprec_from),
                                self._format(total_asset_amount_to - total_asset_deprec_from)],
                    'level': 1,
                })
                lines += domain_lines
                # Append to grand total
                total_amount_from += total_asset_amount_from
                total_amount_to += total_asset_amount_to
                total_amount_plus += total_asset_amount_plus
                total_amount_minus += total_asset_amount_minus

                total_deprec_from += total_asset_deprec_from
                total_deprec_to += total_asset_deprec_to
                total_deprec_plus += total_asset_deprec_plus
                total_deprec_minus += total_asset_deprec_minus

        grand_total_line.append({
                    'id': 999999999,
                    'type': 'o_account_reports_domain_total',
                    'name': 'Grand Total',
                    'footnotes': [],
                    'columns': ['', '', '', '', '', '',
                                self._format(total_amount_from), self._format(total_amount_plus),
                                self._format(total_amount_minus), self._format(total_amount_to),
                                self._format(total_deprec_from), self._format(total_deprec_plus),
                                self._format(total_deprec_minus), self._format(total_deprec_from),
                                self._format(total_amount_to - total_deprec_from)],
                    'level': 1,
        })
        lines += grand_total_line

        return lines


class AccountContextDepreciationSchedule(models.TransientModel):
    _name = "account.context.depreciation.schedule"
    _description = "A particular context for depreciation schedule report"
    _inherit = "account.report"

    fold_field = 'unfolded_categories'
    unfolded_categories = fields.Many2many('account.asset.category', 'context_to_category', string="Unfolded lines")

    def get_report_obj(self):
        return self.env['account.depreciation.schedule']

    def get_columns_names(self):
        """ Returns report table header as a list  """
        context = self.env.context
        date_from = context.get('date_from', _("from"))
        date_to = context.get('date_to', _("to"))
        return [
            _("Code"),
            _("Category"),
            _("M"),
            _("%"),
            _("F"),
            _("Acq."),
            date_from,
            "+",
            "-",
            date_to,
            date_from,
            "+",
            "-",
            date_to,
            _("Net Values"),
        ]

    @api.multi
    def get_columns_types(self):
        """ Type from columns defined above (allowed types: text, date, number) """
        return [
            "text",
            "text",
            "text",
            "number",
            "text",
            "date",
            "number",
            "number",
            "number",
            "number",
            "number",
            "number",
            "number",
            "number",
            "number",
        ]

    def _report_name_to_report_model(self):
        """ Override so our custom model is know need to add our model here """
        map_n2rm = super(AccountContextDepreciationSchedule, self)._report_name_to_report_model()
        map_n2rm['depreciation_schedule'] = 'account.depreciation.schedule'
        return map_n2rm

    def _report_model_to_report_context(self):
        """ Override this one too so we can register our custom model """
        map_m2rc = super(AccountContextDepreciationSchedule, self)._report_model_to_report_context()
        map_m2rc['account.depreciation.schedule'] = 'account.context.depreciation.schedule'
        return map_m2rc
