from odoo import models, fields, api

import ast
import logging

_logger = logging.getLogger(__name__)

class be_vat_checks(models.TransientModel):
    _name = "be.vat.checks"

    company_id = fields.Many2one('res.company',
        string="Company", required=True)
    date_from = fields.Date(string="Start Date", required=True)
    date_to = fields.Date(string="End Date", required=True)
    check_result = fields.Text(string='Check Results', readonly=True)

    @api.multi
    def compute_cheks(self):
        # domains
        domain_01 = self.get_domain_for_code('BETAX01')
        domain_02 = self.get_domain_for_code('BETAX02')
        domain_03 = self.get_domain_for_code('BETAX03')
        domain_49 = self.get_domain_for_code('BETAX49')
        domain_54 = self.get_domain_for_code('BETAX54')
        domain_55 = self.get_domain_for_code('BETAX55')
        domain_56 = self.get_domain_for_code('BETAX56')
        domain_57 = self.get_domain_for_code('BETAX57')
        domain_59 = self.get_domain_for_code('BETAX59')
        domain_63 = self.get_domain_for_code('BETAX63')
        domain_64 = self.get_domain_for_code('BETAX64')
        domain_81 = self.get_domain_for_code('BETAX81')
        domain_82 = self.get_domain_for_code('BETAX82')
        domain_83 = self.get_domain_for_code('BETAX83')
        domain_84 = self.get_domain_for_code('BETAX84')
        domain_85 = self.get_domain_for_code('BETAX85')
        domain_86 = self.get_domain_for_code('BETAX86')
        domain_87 = self.get_domain_for_code('BETAX87')
        domain_88 = self.get_domain_for_code('BETAX88')

        text = "Checks done:\n"
        # Check 1
        if ((len(self.env['account.move.line'].search(domain_01)) > 0) or (len(self.env['account.move.line'].search(domain_02)) > 0) or (len(self.env['account.move.line'].search(domain_03)) > 0)):
            text += "01) : [01] and/or [02] and/or [03], so [54]"
            if (len(self.env['account.move.line'].search(domain_54)) > 0):
                text += "   => OK\n"
            else:
                text += "   => ERROR\n"

        # Check 2
        if (len(self.env['account.move.line'].search(domain_54)) > 0):
            text += "02) : [54], so [01] and/or [02] and/or [03]"
            if ((len(self.env['account.move.line'].search(domain_01)) > 0) or (len(self.env['account.move.line'].search(domain_02)) > 0) or (len(self.env['account.move.line'].search(domain_03)) > 0)):
                text += "   => OK\n"
            else:
                text += "   => ERROR\n"

        # Check 3
        if (len(self.env['account.move.line'].search(domain_55)) > 0):
            text += "03) : [55], so [84] and/or [86] and/or [88]"
            if ((len(self.env['account.move.line'].search(domain_84)) > 0) or (len(self.env['account.move.line'].search(domain_86)) > 0) or (len(self.env['account.move.line'].search(domain_88)) > 0)):
                text += "   => OK\n"
            else:
                text += "   => ERROR\n"

        # Check 4
        if (len(self.env['account.move.line'].search(domain_56)) > 0):
            text += "04) : [56], so [85] and/or [87]"
            if ((len(self.env['account.move.line'].search(domain_85)) > 0) or (len(self.env['account.move.line'].search(domain_87)) > 0)):
                text += "   => OK\n"
            else:
                text += "   => ERROR\n"

        # Check 5
        if (len(self.env['account.move.line'].search(domain_57)) > 0):
            text += "05) : [57], so [85] and/or [87]"
            if ((len(self.env['account.move.line'].search(domain_85)) > 0) or (len(self.env['account.move.line'].search(domain_87)) > 0)):
                text += "   => OK\n"
            else:
                text += "   => ERROR\n"

        # Check 6
        if (len(self.env['account.move.line'].search(domain_59)) > 0):
            text += "06) : [59], so [81] and/or [82] and/or [83] and/or [84] and/or [85]"
            if ((len(self.env['account.move.line'].search(domain_81)) > 0) or (len(self.env['account.move.line'].search(domain_82)) > 0) or (len(self.env['account.move.line'].search(domain_83)) > 0) or (len(self.env['account.move.line'].search(domain_84)) > 0) or (len(self.env['account.move.line'].search(domain_85)) > 0)):
                text += "   => OK\n"
            else:
                text += "   => ERROR\n"

        # Check 7
        if (len(self.env['account.move.line'].search(domain_63)) > 0):
            text += "07) : [63], so [85]"
            if ((len(self.env['account.move.line'].search(domain_85)) > 0)):
                text += "   => OK\n"
            else:
                text += "   => ERROR\n"

        # Check 8
        if (len(self.env['account.move.line'].search(domain_64)) > 0):
            text += "08) : [64], so [49]"
            if ((len(self.env['account.move.line'].search(domain_49)) > 0)):
                text += "   => OK\n"
            else:
                text += "   => ERROR\n"

        # Check 9
        if (len(self.env['account.move.line'].search(domain_87)) > 0):
            text += "09) : [87], so [56] and/or [57]"
            if ((len(self.env['account.move.line'].search(domain_56)) > 0) or (len(self.env['account.move.line'].search(domain_57)) > 0)):
                text += "   => OK\n"
            else:
                text += "   => ERROR\n"

        # Check 10
        if (len(self.env['account.move.line'].search(domain_86)) > 0) or (len(self.env['account.move.line'].search(domain_88)) > 0):
            text += "10) : [86] and/or [88], so [55]"
            if ((len(self.env['account.move.line'].search(domain_55)) > 0)):
                text += "   => OK\n"
            else:
                text += "   => ERROR\n"

        # Check 11
        if (len(self.env['account.move.line'].search(domain_86)) > 0) or (len(self.env['account.move.line'].search(domain_87)) > 0) or (len(self.env['account.move.line'].search(domain_88)) > 0):
            text += "11) : [86] and/or [87] and/or [88], so [81] and/or [82] and/or [83]"
            if (len(self.env['account.move.line'].search(domain_81)) > 0) or (len(self.env['account.move.line'].search(domain_82)) > 0) or (len(self.env['account.move.line'].search(domain_83)) > 0):
                text += "   => OK\n"
            else:
                text += "   => ERROR\n"

        # Check 12
        text += "12) : [01] * 0.06 + [02] * 0.12 + [03] * 0.21 = [54]"
        balance_01 = round(self.get_balance_for_domain(domain_01) * 0.06, 2)
        balance_02 = round(self.get_balance_for_domain(domain_02) * 0.12, 2)
        balance_03 = round(self.get_balance_for_domain(domain_03) * 0.21, 2)
        balance_54 = round(self.get_balance_for_domain(domain_54), 2)
        if (balance_54 - (balance_01 + balance_02 + balance_03) < 0.1):
            text += "   => OK\n"
        else:
            text += "   => ERROR\n"

        # Check 13
        text += "13) : [55] <= ([84] + [86] + [88]) * 0.21"
        balance_55 = self.get_balance_for_domain(domain_55)
        balance_84 = round(self.get_balance_for_domain(domain_84), 2)
        balance_86 = round(self.get_balance_for_domain(domain_86), 2)
        balance_88 = round(self.get_balance_for_domain(domain_88), 2)
        if (balance_55 <= ((balance_84 + balance_86 + balance_88) * 0.21)):
            text += "   => OK\n"
        else:
            text += "   => ERROR\n"

        # Check 14
        text += "14) : [56] + [57] <= ([85] + [87]) * 0.21"
        balance_56 = round(self.get_balance_for_domain(domain_56), 2)
        balance_57 = round(self.get_balance_for_domain(domain_57), 2)
        balance_85 = round(self.get_balance_for_domain(domain_85), 2)
        balance_87 = round(self.get_balance_for_domain(domain_87), 2)
        if (balance_56 + balance_57 <= ((balance_85 + balance_87) * 0.21)):
            text += "   => OK\n"
        else:
            text += "   => ERROR\n"

        # Check 15
        text += "15) : [59] <= ([81] + [82] + [83] + [84] + [85]) * 0.21"
        balance_59 = self.get_balance_for_domain(domain_59)
        balance_81 = round(self.get_balance_for_domain(domain_81), 2)
        balance_82 = round(self.get_balance_for_domain(domain_82), 2)
        balance_83 = round(self.get_balance_for_domain(domain_83), 2)
        balance_84 = round(self.get_balance_for_domain(domain_84), 2)
        balance_85 = round(self.get_balance_for_domain(domain_85), 2)
        if (balance_59 <= ((balance_81 + balance_82 + balance_83 + balance_84 + balance_85) * 0.21)):
            text += "   => OK\n"
        else:
            text += "   => ERROR\n"

        # Check 16
        text += "16) : [63] <= [85] * 0.21"
        balance_63 = round(self.get_balance_for_domain(domain_63), 2)
        balance_85 = round(self.get_balance_for_domain(domain_85), 2)
        if (balance_63 <= round(balance_85 * 0.21, 2)):
            text += "   => OK\n"
        else:
            text += "   => ERROR\n"

        # Check 17
        text += "17) : [64] <= [49] * 0.21"
        balance_64 = round(self.get_balance_for_domain(domain_64), 2)
        balance_49 = round(self.get_balance_for_domain(domain_49), 2)
        if (balance_64 - (balance_49 * 0.21) < 0.1):
            text += "   => OK\n"
        else:
            text += "   => ERROR\n"

        self.check_result = text

        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'be.vat.checks',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            }

    def get_domain_for_code(self, code):
        lines = self.env['account.financial.html.report.line'].search([['code', '=like', code]])
        if (len(lines) > 0):
            line = lines[0]
            domain = ast.literal_eval(line.domain)
            domain.append(('date', '>=', self.date_from))
            domain.append(('date', '<=', self.date_to))
            return domain
        return [[]]

    def get_balance_for_domain(self, domain):
        lines = self.env['account.move.line'].search(domain)
        balance = 0
        for line in lines:
            balance += line.balance
        if balance < 0:
            balance = balance * -1
        return balance
