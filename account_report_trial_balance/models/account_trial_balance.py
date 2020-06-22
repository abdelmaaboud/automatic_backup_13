from odoo import models, api, _, fields
from odoo.tools.misc import formatLang, format_date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, float_is_zero
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class ReportTrialBalance(models.AbstractModel):
    _inherit = "account.coa.report"
    
    @api.model
    def get_lines(self, options, line_id=None):
        context = self.env.context
        company_id = context.get('company_id') or self.env.user.company_id
        grouped_accounts = {}
        initial_balances = {}
        comparison_table = [options.get('date')]
        comparison_table += options.get('comparison') and options['comparison'].get('periods') or []

        #get the balance of accounts for each period
        period_number = 0
        for period in reversed(comparison_table):
            res = self.with_context(date_from_aml=period['date_from'], date_to=period['date_to'], date_from=period['date_from'] and company_id.compute_fiscalyear_dates(datetime.strptime(period['date_from'], "%Y-%m-%d"))['date_from'] or None).group_by_account_id(options, line_id)  # Aml go back to the beginning of the user chosen range but the amount on the account line should go back to either the beginning of the fy or the beginning of times depending on the account
            # Put the initial balance for all lines at zero for account with code starting with 6 or 7
            for account in res:
                if account.code[0] in ('6', '7'):
                    res[account].update({
                        'balance': float(res[account]['balance']) - float(res[account]['initial_bal']['balance']),
                        'amount_currency': float(res[account]['amount_currency']) - float(res[account]['initial_bal']['amount_currency']),
                        'debit': float(res[account]['debit']) - float(res[account]['initial_bal']['debit']),
                        'credit': float(res[account]['credit']) - float(res[account]['initial_bal']['credit'])
                    })
                    res[account]['initial_bal'].update({
                        'balance': 0.0,
                        'amount_currency': 0.0,
                        'debit': 0.0,
                        'credit': 0.0
                    })
            if period_number == 0:
                initial_balances = dict([(k, res[k]['initial_bal']['balance']) for k in res])
            for account in res:
                if account not in grouped_accounts:
                    grouped_accounts[account] = [{'balance': 0, 'debit': 0, 'credit': 0} for p in comparison_table]
                grouped_accounts[account][period_number]['balance'] = res[account]['balance'] - res[account]['initial_bal']['balance']
                grouped_accounts[account][period_number]['debit'] = res[account]['debit'] - res[account]['initial_bal']['debit']
                grouped_accounts[account][period_number]['credit'] = res[account]['credit'] - res[account]['initial_bal']['credit']
            period_number += 1

        #build the report
        lines = self._post_process(grouped_accounts, initial_balances, options, comparison_table)
        return lines