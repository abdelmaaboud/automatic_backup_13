{
    'name': 'Luxembourg - VAT Intra Report',
    'version': '1.0.0',
    'category': 'Localization',
    'author': 'ABAKUS IT-SOLUTIONS',
    'description': """
Partner VAT Intra report for Luxembourg
    - Partner VAT Intra
    
To make it work, add 2 lines in:
account_reports/models/account_report_context_common.py
- 'l10n_lu_partner_vat_intra': 'l10n.lu.report.partner.vat.intra', in def _report_name_to_report_model(self):
- 'l10n.lu.report.partner.vat.intra': 'l10n.lu.partner.vat.intra.context', in def _report_model_to_report_context(self):
This module is a LU version of the l10n_be_reports from Odoo
    """,
    'depends': [
        'l10n_lu', 
        'account_reports'
    ],
    'data': [
        'views/report_vat_statement.xml'
    ],
    'installable': True,
    'website': 'https://www.abakusitsolutions.eu',
}