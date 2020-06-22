from odoo import models, api, _, fields
from odoo.tools.misc import formatLang, format_date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, float_is_zero
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class ReportPartnerLedger(models.AbstractModel):
    _inherit = "account.partner.ledger"
    
    def do_query(self, options, line_id):
        # We are not going to return the super
        res = super(ReportPartnerLedger, self).do_query(options, line_id)
        
        account_types = [a.get('id') for a in options.get('account_type') if a.get('selected', False)]
        if not account_types:
            account_types = [a.get('id') for a in options.get('account_type')]
        # Create the currency table.
        user_company = self.env.user.company_id
        companies = self.env['res.company'].search([])
        rates_table_entries = []
        for company in companies:
            if company.currency_id == user_company.currency_id:
                rate = 1.0
            else:
                rate = user_company.currency_id.rate / company.currency_id.rate
            rates_table_entries.append((company.id, rate, user_company.currency_id.decimal_places))
        currency_table = ','.join('(%s, %s, %s)' % r for r in rates_table_entries)
        with_currency_table = 'WITH currency_table(company_id, rate, precision) AS (VALUES %s)' % currency_table

        # Sum query
        debit_field = 'debit_cash_basis' if options.get('cash_basis') else 'debit'
        credit_field = 'credit_cash_basis' if options.get('cash_basis') else 'credit'
        balance_field = 'balance_cash_basis' if options.get('cash_basis') else 'balance'
        tables, where_clause, params = self.env['account.move.line']._query_get(
            [('account_id.internal_type', 'in', account_types)])
        query = '''
            SELECT
                \"account_move_line\".partner_id,
                SUM(ROUND(\"account_move_line\".''' + debit_field + ''' * currency_table.rate, currency_table.precision))     AS debit,
                SUM(ROUND(\"account_move_line\".''' + credit_field + ''' * currency_table.rate, currency_table.precision))    AS credit,
                SUM(ROUND(\"account_move_line\".''' + balance_field + ''' * currency_table.rate, currency_table.precision))   AS balance
            FROM %s
            LEFT JOIN currency_table                    ON currency_table.company_id = \"account_move_line\".company_id
            WHERE %s
            AND \"account_move_line\".partner_id IS NOT NULL
            GROUP BY \"account_move_line\".partner_id
        ''' % (tables, where_clause)
        if line_id:
            query = query.replace('WHERE', 'WHERE \"account_move_line\".partner_id = %s AND ')
            params = [str(line_id)] + params
        if options.get("unreconciled"):
            query = query.replace("WHERE", '''WHERE (\"account_move_line\".full_reconcile_id IS NULL
            OR \"account_move_line\".full_reconcile_id NOT IN 
            (SELECT id 
            FROM \"account_full_reconcile\" 
            WHERE (create_date<='%s' AND create_date>='%s') )) AND ''' % (options['date']['date_to'], options['date']['date_from']))
        self._cr.execute(with_currency_table + query, params)
        query_res = self._cr.dictfetchall()
        return dict((res['partner_id'], res) for res in query_res)
    
    def group_by_partner_id(self, options, line_id):
        # We are not going to return the super
        res = super(ReportPartnerLedger, self).group_by_partner_id(options, line_id)
        
        partners = {}
        account_types = [a.get('id') for a in options.get('account_type') if a.get('selected', False)]
        if not account_types:
            account_types = [a.get('id') for a in options.get('account_type')]
        date_from = options['date']['date_from']
        results = self.do_query(options, line_id)
        initial_bal_date_to = datetime.strptime(date_from, DEFAULT_SERVER_DATE_FORMAT) + timedelta(days=-1)
        initial_bal_results = self.with_context(date_from=False, date_to=initial_bal_date_to.strftime(DEFAULT_SERVER_DATE_FORMAT)).do_query(options, line_id)
        context = self.env.context
        base_domain = [('date', '<=', context['date_to']), ('company_id', 'in', context['company_ids']), ('account_id.internal_type', 'in', account_types)]
        base_domain.append(('date', '>=', date_from))
        if context['state'] == 'posted':
            base_domain.append(('move_id.state', '=', 'posted'))
        if options.get('unreconciled'):
            account_full_reconciles = options.get('account_full_reconciles')
            if account_full_reconciles:
                base_domain.append(('|'))
                base_domain.append(('full_reconcile_id', '=', False))
                base_domain.append(('full_reconcile_id.id', 'not in', account_full_reconciles ))
            else:
                base_domain.append(('full_reconcile_id', '=', False))
        for partner_id, result in results.items():
            domain = list(base_domain)  # copying the base domain
            domain.append(('partner_id', '=', partner_id))
            partner = self.env['res.partner'].browse(partner_id)
            partners[partner] = result
            partners[partner]['initial_bal'] = initial_bal_results.get(partner.id, {'balance': 0, 'debit': 0, 'credit': 0})
            partners[partner]['balance'] += partners[partner]['initial_bal']['balance']
            if not context.get('print_mode'):
                #  fetch the 81 first amls. The report only displays the first 80 amls. We will use the 81st to know if there are more than 80 in which case a link to the list view must be displayed.
                partners[partner]['lines'] = self.env['account.move.line'].search(domain, order='date', limit=81)
            else:
                partners[partner]['lines'] = self.env['account.move.line'].search(domain, order='date')

        # Add partners with an initial balance != 0 but without any AML in the selected period.
        prec = self.env.user.company_id.currency_id.rounding
        missing_partner_ids = set(initial_bal_results.keys()) - set(results.keys())
        for partner_id in missing_partner_ids:
            if not float_is_zero(initial_bal_results[partner_id]['balance'], precision_rounding=prec):
                partner = self.env['res.partner'].browse(partner_id)
                partners[partner] = {'balance': 0, 'debit': 0, 'credit': 0}
                partners[partner]['initial_bal'] = initial_bal_results[partner_id]
                partners[partner]['balance'] += partners[partner]['initial_bal']['balance']
                partners[partner]['lines'] = self.env['account.move.line']

        return partners
    
    
    @api.model
    def get_lines(self, options, line_id=None):
        # We are not going to return the super
        res = super(ReportPartnerLedger, self).get_lines(options, line_id)
        
        lines = []
        if line_id:
            line_id = line_id.replace('partner_', '')
        context = self.env.context
        company_id = context.get('company_id') or self.env.user.company_id

        #If a default partner is set, we only want to load the line referring to it.
        if options.get('partner_id'):
            line_id = options['partner_id']

        account_full_reconciles = self.env['account.full.reconcile'].search([("create_date", '<=', context['date_to']), ("create_date", '>=', context['date_from'])]).ids
        options['account_full_reconciles'] = account_full_reconciles
            
        grouped_partners = self.group_by_partner_id(options, line_id)
        sorted_partners = sorted(grouped_partners, key=lambda p: p.name or '')
        unfold_all = context.get('print_mode') and not options.get('unfolded_lines') or options.get('partner_id')
        total_initial_balance = total_debit = total_credit = total_balance = 0.0
        for partner in sorted_partners:
            debit = grouped_partners[partner]['debit']
            credit = grouped_partners[partner]['credit']
            balance = grouped_partners[partner]['balance']
            initial_balance = grouped_partners[partner]['initial_bal']['balance']
            total_initial_balance += initial_balance
            total_debit += debit
            total_credit += credit
            total_balance += balance
            lines.append({
                'id': 'partner_' + str(partner.id),
                'name': partner.name,
                'columns': [{'name': v} for v in [self.format_value(initial_balance), self.format_value(debit), self.format_value(credit), self.format_value(balance)]],
                'level': 2,
                'trust': partner.trust,
                'unfoldable': True,
                'unfolded': 'partner_' + str(partner.id) in options.get('unfolded_lines') or unfold_all,
                'colspan': 5,
            })
            used_currency = self.env.user.company_id.currency_id
            if 'partner_' + str(partner.id) in options.get('unfolded_lines') or unfold_all:
                progress = initial_balance
                domain_lines = []
                amls = grouped_partners[partner]['lines']
                too_many = False
                if len(amls) > 80 and not context.get('print_mode'):
                    amls = amls[:80]
                    too_many = True
                for line in amls:
                    if options.get('cash_basis'):
                        line_debit = line.debit_cash_basis
                        line_credit = line.credit_cash_basis
                    else:
                        line_debit = line.debit
                        line_credit = line.credit
                    line_currency = line.company_id.currency_id.with_context(date=amls.env.context.get('date') or fields.Date.today())
                    line_debit = line_currency.compute(line_debit, used_currency)
                    line_credit = line_currency.compute(line_credit, used_currency)
                    progress_before = progress
                    progress = progress + line_debit - line_credit
#                     name = '-'.join(
#                         (line.move_id.name not in ['', '/'] and [line.move_id.name] or []) +
#                         (line.ref not in ['', '/', False] and [line.ref] or []) +
#                         ([line.name] if line.name and line.name not in ['', '/'] else [])
#                     )
                    name = line.move_id.name not in ['', '/'] and line.move_id.name or line.name
                    if len(name) > 35 and not self.env.context.get('no_format'):
                        name = name[:32] + "..."
                    caret_type = 'account.move'
                    if line.invoice_id:
                        caret_type = 'account.invoice.in' if line.invoice_id.type in ('in_refund', 'in_invoice') else 'account.invoice.out'
                    elif line.payment_id:
                        caret_type = 'account.payment'
                    domain_lines.append({
                        'id': line.id,
                        'parent_id': 'partner_' + str(partner.id),
                        'name': format_date(self.env, line.date),
                        'columns': [{'name': v} for v in [line.journal_id.code, line.account_id.code, name, line.full_reconcile_id.name, self.format_value(progress_before),
                                    line_debit != 0 and self.format_value(line_debit) or '',
                                    line_credit != 0 and self.format_value(line_credit) or '',
                                    self.format_value(progress)]],
                        'caret_options': caret_type,
                        'level': 4,
                    })
                if too_many:
                    domain_lines.append({
                        'id': 'too_many_' + str(partner.id),
                        'parent_id': 'partner_' + str(partner.id),
                        'action': 'view_too_many',
                        'action_id': 'partner,%s' % (partner.id,),
                        'name': _('There are more than 80 items in this list, click here to see all of them'),
                        'colspan': 8,
                        'columns': [{}],
                    })
                lines += domain_lines
        if not line_id:
            lines.append({
                'id': 'grouped_partners_total',
                'name': _('Total'),
                'level': 0,
                'class': 'o_account_reports_domain_total',
                'columns': [{'name': v} for v in ['', '', '', '', self.format_value(total_initial_balance), self.format_value(total_debit), self.format_value(total_credit), self.format_value(total_balance)]],
            })
        return lines