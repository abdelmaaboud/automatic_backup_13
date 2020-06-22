from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)


class account_analytic_account(models.Model):
    _inherit = ['account.analytic.account']

    parent_account_id = fields.Many2one('account.analytic.account', string="Parent Account")
    child_account_ids = fields.One2many('account.analytic.account', 'parent_account_id', string="Children Accounts")

    structured_name = fields.Char(string="Structured name", compute='_computeStructuredName')
    structured_type = fields.Selection([('parent', 'Parent'), ('account', 'Account')], string="Structured Type")

    # Totals
    structured_credit = fields.Monetary(string="Structured Credit", compute="compute_debit_credit_balance")
    structured_debit = fields.Monetary(string="Structured Debit", compute="compute_debit_credit_balance")
    structured_balance = fields.Monetary(string="Structured Balance", compute="compute_debit_credit_balance")

    # For direct lines
    lines_credit = fields.Monetary(string="Credit for account", compute="compute_debit_credit_balance")
    lines_debit = fields.Monetary(string="Debit for account", compute="compute_debit_credit_balance")
    lines_balance = fields.Monetary(string="Balance for account", compute="compute_debit_credit_balance")

    # For child accounts
    child_account_ids_credit = fields.Monetary(string="Credit for children", compute="compute_debit_credit_balance")
    child_account_ids_debit = fields.Monetary(string="Debit for children", compute="compute_debit_credit_balance")
    child_account_ids_balance = fields.Monetary(string="Balance for children", compute="compute_debit_credit_balance")

    @api.one
    def compute_debit_credit_balance(self):
        if self.structured_type == 'parent':
            # Compute c and d for its lines
            debitcredit = self.get_debit_and_credit()[0]
            self.lines_debit = debitcredit[0]
            self.lines_credit = debitcredit[1]
            self.lines_balance = self.lines_credit - self.lines_debit

            # Then compute for the sub accounts
            self.child_account_ids_debit = 0
            self.child_account_ids_credit = 0
            for sub_account in self.child_account_ids:
                sub_account.compute_debit_credit_balance()
                self.child_account_ids_debit += sub_account.structured_debit
                self.child_account_ids_credit += sub_account.structured_credit
            self.child_account_ids_balance = self.child_account_ids_credit - self.child_account_ids_debit

        else:
            # Compute for the sub accounts
            self.child_account_ids_debit = 0
            self.child_account_ids_credit = 0
            self.child_account_ids_balance = 0

            # Compute c and d for its lines
            debitcredit = self.get_debit_and_credit()[0]
            self.lines_debit = debitcredit[0]
            self.lines_credit = debitcredit[1]
            self.lines_balance = self.lines_credit - self.lines_debit

        # Structured: lines + child accounts
        self.structured_debit = self.lines_debit + self.child_account_ids_debit
        self.structured_credit = self.lines_credit + self.child_account_ids_credit
        self.structured_balance = self.structured_credit - self.structured_debit

    @api.one
    def get_debit_and_credit(self):
        from_date = self._context.get('from_date')
        to_date = self._context.get('to_date')

        analytic_line_obj = self.env['account.analytic.line']
        domain = [('account_id', '=', self.id), ('move_id', '!=', False)]
        if from_date:
            domain.append(('date', '>=', from_date))
        if to_date:
            domain.append(('date', '<=', to_date))

        account_amounts = analytic_line_obj.search_read(domain, ['account_id', 'amount'])
        account_ids = set([line['account_id'][0] for line in account_amounts])
        data_debit = {account_id: 0.0 for account_id in account_ids}
        data_credit = {account_id: 0.0 for account_id in account_ids}
        for account_amount in account_amounts:
            if account_amount['amount'] < 0.0:
                data_debit[account_amount['account_id'][0]] += account_amount['amount']
            else:
                data_credit[account_amount['account_id'][0]] += account_amount['amount']
        debitcredit = [abs(data_debit.get(self.id, 0.0)), data_credit.get(self.id, 0.0)]

        return debitcredit

    @api.one
    @api.depends('parent_account_id')
    def _computeStructuredName(self):
        if not self.parent_account_id:
            self.structured_name = self.name
            return self.name

        full_name = self.name
        parent = self.parent_account_id
        while parent:
            full_name = parent.name + " \ " + full_name
            parent = parent.parent_account_id

        self.structured_name = full_name
        return full_name

    @api.multi
    def print_account_report(self):
        datas = {
            'ids': [self.id],
            'model': 'account.analytic.account',
            'context': self._context,
        }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'account_analytic_structuring.analytic_structured_report',
            'datas': datas,
        }
