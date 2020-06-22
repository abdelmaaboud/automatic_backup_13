# -*- coding: utf-8 -*-

from odoo import models, api, _
from odoo.tools.misc import formatLang
import logging
_logger = logging.getLogger(__name__)

class ReportL10nLuPartnerVatIntra(models.AbstractModel):
    _name = "l10n.lu.report.partner.vat.intra"
    _description = "Partner VAT Intra"
    _inherit= "account.report"
    
    filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_month'}

    @api.model
    def get_lines(self, options, line_id=None, get_xml_data=False):
        _logger.info("\n\n CALLED")
        lines = []
        seq = amount_sum = 0
        company_clause = 'AND FALSE'
        context_id = self.env.context
        if context_id['company_ids']:
            company_ids = '(' + ','.join(map(str, context_id['company_ids'])) + ')'
            company_clause = 'AND l.company_id IN ' + company_ids
        ids = [
            self.env.ref('__export__.account_tax_49').id,
            self.env.ref('__export__.account_tax_55').id,
        ]
        tag_ids = []
        #tags_browsed = self.env['ir.model.data'].browse(ids)
        for tag in ids:
            tag_id = self.env['ir.model.data'].browse(tag.id)[0].res_id
            _logger.debug("Tag: %s", tag_id)
            tag_ids.append(tag_id)
        _logger.debug("\n\n\nTags - IDS : %s", tag_ids)
        self.env.cr.execute('''SELECT p.name As partner_name, l.partner_id AS partner_id, p.vat AS vat,
                      tt.account_account_tag_id AS intra_code, SUM(-l.balance) AS amount
                      FROM account_move_line l
                      LEFT JOIN res_partner p ON l.partner_id = p.id
                      LEFT JOIN account_move_line_account_tax_rel amlt ON l.id = amlt.account_move_line_id
                      LEFT JOIN account_tax_account_tag tt on amlt.account_tax_id = tt.account_tax_id
                      WHERE tt.account_account_tag_id IN %s
                       AND l.date >= '%s'
                       AND l.date <= '%s'
                       %s
                      GROUP BY p.name, l.partner_id, p.vat, intra_code''' % (tuple(tag_ids), context_id['date_from'], context_id['date_to'], company_clause))
#
        p_count = 0

        for row in self.env.cr.dictfetchall():
            if not row['vat']:
                row['vat'] = ''
                p_count += 1

            amt = row['amount'] or 0.0
            if amt:
                seq += 1
                amount_sum += amt

                [intra_code, code] = row['intra_code'] == tag_ids[0] and ['VB', 'L'] or (row['intra_code'] == tag_ids[1] and ['VP', 'S']) or ['', '']

                columns = [row['vat'].replace(' ', '').upper(), code, intra_code, amt]
                if not self.env.context.get('no_format', False):
                    currency_id = self.env.user.company_id.currency_id
                    columns[3] = formatLang(self.env, columns[3], currency_obj=currency_id)

                lines.append({
                    'id': row['partner_id'],
                    'type': 'partner_id',
                    'name': row['partner_name'],
                    'footnotes': context_id._get_footnotes('partner_id', row['partner_id']),
                    'columns': columns,
                    'level': 2,
                    'unfoldable': False,
                    'unfolded': False,
                })

        if get_xml_data:
            return {'lines': lines, 'clientnbr': str(seq), 'amountsum': round(amount_sum, 2), 'partner_wo_vat': p_count}
        return lines

    @api.model
    def get_title(self):
        return _('Partner VAT Intra')

    @api.model
    def get_name(self):
        return 'l10n_lu_partner_vat_intra'

    @api.model
    def get_report_type(self):
        return 'no_comparison'
    
    def _get_columns_name(self, options):
        return [_('VAT Number'), _('Code'), _('Intra Code'), _('Amount')]
    
    def get_report_obj(self):
        return self.env['l10n.lu.report.partner.vat.intra']

    @api.model
    def get_template(self):
        return 'account_reports.report_financial'