# -*- coding: utf-8 -*-
# (c) 2018 - AbAKUS IT SOLUTIONS

import logging
from pprint import pformat
from odoo import models, api, fields, _
import datetime

_logger = logging.getLogger(__name__)


class ReportAccountDepreciationSchedule(models.AbstractModel):
    _name = 'depreciation.schedule.report'
    _inherit = 'account.report'

    filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_month'}
    filter_unfold_all = True

    def get_columns_name(self, options):
        """ Returns report table header as a list  """
        date_from = options['date'].get('date_from', _("from"))
        date_to = options['date'].get('date_to', _("to"))
        if date_from != "from":
            date_from = fields.Date.to_string(datetime.datetime.strptime(date_from, '%Y-%m-%d'))
        if date_to != "to":
            date_to = fields.Date.to_string(datetime.datetime.strptime(date_to, '%Y-%m-%d'))
        return [
            {'name': ""},
            {'name': _("Code")},
            {'name': _("Category")},
            {'name': _("M")},
            {'name': _("%"), 'class': "number"},
            {'name': _("F")},
            {'name': _("Acq.")},
            {'name': date_from, 'class': "number"},
            {'name': "+", 'class': "number"},
            {'name': "-", 'class': "number"},
            {'name': date_to, 'class': "number"},
            {'name': date_from, 'class': "number"},
            {'name': "+", 'class': "number"},
            {'name': "-", 'class': "number"},
            {'name': date_to, 'class': "number"},
            {'name': _("Net Values"), 'class': "number"}
        ]

    @api.model
    def get_lines(self, options, line_id=None):
        """ Returns report lines. When line_id is passed we are unfolding to access a sub line """
        lines = []
        companies = [c['id'] for c in options['multi_company'] if c['selected']]
        # first group by categories
        category_obj = self.env['account.asset.category']
        category_ids = category_obj.search([('company_id', 'in', companies)])
        # Full addition:
        total_amount_from = total_amount_to = 0.0
        total_amount_plus = total_amount_minus = 0.0

        total_deprec_from = total_deprec_to = 0.0
        total_deprec_plus = total_deprec_minus = 0.0
        grand_total_line = []
        for cat in category_ids:
            # Category line
            _logger.info('\n\nname %s' % str(cat.account_asset_id.code + " " + cat.display_name + " (" + options['date'].get('date_from') + " to " + options['date'].get('date_to') + ")"))
            if not line_id or line_id == cat.id:
                lines.append(
                    {
                        'id': cat.id,
                        'name': str(cat.account_asset_id.code + " " +
                                cat.display_name + " (" +
                                options['date'].get('date_from') + " to " +
                                options['date'].get('date_to') + ")"),
                        'columns': [],
                        'level': 2,
                        'unfoldable': True,
                        'unfolded': cat.id in options['unfolded_lines'] or options['unfold_all'],
                        'colspan': 16,
                    }
                )
            # Go deeper for each category
            asset_obj = self.env['account.asset.asset']
            # No filtering on dates here since we want all assets
            asset_ids = asset_obj.search([
                ('company_id', 'in', companies),
                ('category_id', '=', cat.id)
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

                if asset.date < options.get('date').get('date_from'):
                    asset_amount_from = asset.value
                elif asset.date <= options.get('date').get('date_to'):
                    asset_amount_plus = asset.value
                
                #TODO: ADD minus method (see when sell an asset)
                
#                 if asset_amount_from < asset_amount_to:
#                     asset_amount_plus = asset_amount_to - asset_amount_from
#                 else:
#                     asset_amount_minus = asset_amount_from - asset_amount_to
                asset_amount_to = asset_amount_from + asset_amount_plus + asset_amount_minus

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
                    if dl.depreciation_date <= options.get('date').get('date_from'):
                        asset_deprec_from += dl.amount
                    elif dl.depreciation_date <= options.get('date').get('date_to'):
                        asset_deprec_plus += dl.amount
                
                #TODO: ADD minus method for deprec (see when sell an asset)
                
#                 if asset_deprec_from < asset_deprec_to:
#                     asset_deprec_plus = asset_deprec_to - asset_deprec_from
#                 else:
#                     asset_deprec_minus = asset_deprec_from - asset_deprec_to

                asset_deprec_to = asset_deprec_from + asset_deprec_plus + asset_deprec_minus
        
                total_asset_deprec_from += asset_deprec_from
                total_asset_deprec_to += asset_deprec_to
                total_asset_deprec_plus += asset_deprec_plus
                total_asset_deprec_minus += asset_deprec_minus
                # Build second level lines
                progress_factor = 100
                if asset.method_number > 0 and asset.method_period > 0:
                    progress_factor = round(100 / ((asset.method_number * asset.method_period) / 12), 2)
                if (line_id and cat.id == line_id) or options['unfold_all']:
                    lines.append(
                        {
                            'id': asset.id,
                            'name': "ASSET/{:04d}".format(asset.id),
                            'parent_id': cat.id,
                            'columns': [
                                {'name': asset.code},
                                {'name': asset.display_name},
                                {'name': "L" if asset.category_id.method == _('linear') else "?"},
                                {'name': progress_factor},
                                {'name': "M"},
                                {'name': asset.date},
                                {'name': asset_amount_from},
                                {'name': self.format_value(asset_amount_plus)},
                                {'name': self.format_value(asset_amount_minus)},
                                {'name': self.format_value(asset_amount_to)},
                                {'name': self.format_value(asset_deprec_from)},
                                {'name': self.format_value(asset_deprec_plus)},
                                {'name': self.format_value(asset_deprec_minus)},
                                {'name': self.format_value(asset_deprec_to)},
                                {'name': self.format_value(asset_amount_to - asset_deprec_to)}
                            ],
                            'level': 2,
                        }
                    )
            if (line_id and line_id == cat.id) or options['unfold_all']:
                lines.append({
                    'id': 999000 + (line_id if line_id else 998),
                    'name': 'Total',
                    'parent_id': cat.id,
                    'columns': [
                        {'name': ''},
                        {'name': ''},
                        {'name': ''},
                        {'name': ''},
                        {'name': ''},
                        {'name': ''},
                        {'name': self.format_value(total_asset_amount_from)},
                        {'name': self.format_value(total_asset_amount_plus)},
                        {'name': self.format_value(total_asset_amount_minus)},
                        {'name': self.format_value(total_asset_amount_to)},
                        {'name': self.format_value(total_asset_deprec_from)},
                        {'name': self.format_value(total_asset_deprec_plus)},
                        {'name': self.format_value(total_asset_deprec_minus)},
                        {'name': self.format_value(total_asset_deprec_to)},
                        {'name': self.format_value(total_asset_amount_to - total_asset_deprec_to)}
                    ],
                    'level': 2,
                })

            # Append to grand total
            total_amount_from += total_asset_amount_from
            total_amount_to += total_asset_amount_to
            total_amount_plus += total_asset_amount_plus
            total_amount_minus += total_asset_amount_minus

            total_deprec_from += total_asset_deprec_from
            total_deprec_to += total_asset_deprec_to
            total_deprec_plus += total_asset_deprec_plus
            total_deprec_minus += total_asset_deprec_minus
        if not line_id:
            lines.append({
                'id': 999999,
#                 'type': 'o_account_reports_domain_total',
                'name': 'Grand Total',
                'columns': [
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': self.format_value(total_amount_from)},
                    {'name': self.format_value(total_amount_plus)},
                    {'name': self.format_value(total_amount_minus)},
                    {'name': self.format_value(total_amount_to)},
                    {'name': self.format_value(total_deprec_from)},
                    {'name': self.format_value(total_deprec_plus)},
                    {'name': self.format_value(total_deprec_minus)},
                    {'name': self.format_value(total_deprec_to)},
                    {'name': self.format_value(total_amount_to - total_deprec_to)}
                ],
                'level': 2,
            })

        return lines

    def get_report_name(self):
        return _("Depreciation Schedule")
