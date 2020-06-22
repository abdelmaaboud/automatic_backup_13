# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
import base64
import datetime
import logging
_logger = logging.getLogger(__name__)

class ImportSalaryWizard(models.TransientModel):
    _name = 'import.salary.wizard'

    file = fields.Binary()

    def prepare_account_move_values(self, date, reference):
        return {
            'date': date,
            'journal_id': int(self.env['ir.config_parameter'].get_param('import_salary_journal_id')),
            'company_id': int(self.env['ir.config_parameter'].get_param('import_salary_company_id')),
            'ref': reference,
            'state': 'draft',
        }

    def action_import_file(self):
        if self.file:
            str_file = base64.b64decode(self.file).decode("ISO-8859-1")
            ref_sequence = False
            account_move_id = False
            lines = []
            for i, line in enumerate(str_file.splitlines()):
                if i == 0:
                    continue
                try:
                    date, account_id, label, analytic_account_id, debit, credit, sequence = self.parse_line(line)
                    if ref_sequence != sequence:
                        if account_move_id:
                            account_move_id.write({'line_ids': lines})
                        ref_sequence = sequence
                        lines = []
                        account_move_id = self.env['account.move'].create(self.prepare_account_move_values(date, _("Salary %s %s %s") % (label.split('-')[0].strip(), date.month, date.year)))
                    if account_move_id:
                        lines += [[0, 0, {
                            'account_id': account_id.id,
                            'name': label,
                            'analytic_account_id': analytic_account_id.id if analytic_account_id else False,
                            'debit': debit,
                            'credit': credit,
                            'currency_id': self.env.user.company_id.currency_id.id
                        }]]
                except exceptions.ValidationError:
                    continue

        if account_move_id and not account_move_id.line_ids and lines:
            account_move_id.write({'line_ids': lines})
        else:
            raise exceptions.Warning(_('You must enter a file to import!'))

    def parse_line(self, line):
        line_array = line.split(";")
        line_array = [s.strip() for s in line_array]
        if line_array[0] and line_array[1] and line_array[2]:
            date = datetime.datetime.strptime(line_array[0], '%Y%m%d').date()
            account_id = self.env['account.account'].search([('code', '=', line_array[1]), ('company_id', '=', int(self.env['ir.config_parameter'].get_param('import_salary_company_id')))], limit=1)
            if not account_id:
                raise exceptions.Warning(_("There is no account with code %s" % line_array[1]))
            label = line_array[2]
            account_analytic_id = self.env['account.analytic.account'].browse(int(line_array[3])) if line_array[3] else False
            debit = float(line_array[4].replace('.', '').replace(',', '.')) if line_array[4] else 0.0
            credit = float(line_array[5].replace('.', '').replace(',', '.')) if line_array[5] else 0.0
            sequence = int(line_array[6])
            return date, account_id, label, account_analytic_id, debit, credit, sequence
        else:
            raise exceptions.ValidationError(_("Problem with parsing"))
