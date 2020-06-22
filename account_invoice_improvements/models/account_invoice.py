from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)

class AccountInvoiceImproved(models.Model):
    _inherit = 'account.invoice'

    next_invoice_number = fields.Char(compute='_compute_next_invoice_number', string="Next document number", store=False)
    comment = fields.Html('Additional Information', readonly=True, states={'draft': [('readonly', False)]})

    _sql_constraints = [
        ('reference_unique',
         'UNIQUE(reference)',
         "The reference must be unique"),
    ]

    @api.one
    @api.depends('journal_id')
    def _compute_next_invoice_number(self):
        if not self.journal_id:
            self.next_invoice_number = "NO JOURNAL SELECTED"
            return

        if self.state in ("", "draft"):
            nn_int = self.journal_id.sequence_id.number_next
            nn_string = str(nn_int)
            
            nn_ex_string = self.env['account.invoice'].search([['journal_id','=',self.journal_id.id],['number', '!=', '']], limit=1).number

            if nn_ex_string:
                l = len(nn_ex_string) - 1
                if l > 0:
                    cpt = 0
                    for i in range(l, 0, -1):
                        if nn_ex_string[i].isnumeric():
                            cpt += 1
                        else:
                            break
                    seq = int(nn_ex_string[-cpt:]) + 1
                    nn = nn_ex_string[:-cpt]
                    self.next_invoice_number = nn + str(seq)
                else:
                    self.next_invoice_number = '1'
            else:
                self.next_invoice_number = '1'
        else:
            self.next_invoice_number = "ERROR"
    
    @api.onchange('supplier_reference')
    def update_reference(self):
        if self.partner_id and self.supplier_reference and len(self.supplier_reference) > 0:
            account_invoices = self.env['account.invoice'].search([('supplier_reference', '=', self.supplier_reference), ('partner_id', '=', self.partner_id.id)])
            if account_invoices:
                self.reference = ""
                raise ValidationError('Supplier Invoice Number Failure - The supplier invoice number already exists')
            else:
                self.reference = self.supplier_reference
        else:
            self.reference = self.supplier_reference

    @api.multi
    def action_invoice_open(self):
        #for line in self.invoice_line_ids:
            # Check if there is a tax on each line
            #if len(line.invoice_line_tax_ids) == 0:
            #    raise ValidationError('No tax! - A line in this invoice does not contain any tax. This is not allowed by the system. Please, correct this.')
            ## Check if there is more than one tax on each line
            #if len(line.invoice_line_tax_ids) > 1:
            #    raise ValidationError('Multiple taxes for one line! - A line in this invoice contains more than one tax. This is not allowed by the system. Please, correct this.')
            ## Check if there is an analytic account on each line
            #if len(line.account_analytic_id) == 0:
            #    raise ValidationError('No Analytic Account! - A line in this invoice does not contain an analytic account. This is not allowed by the system. Please, correct this.')

        res = super(AccountInvoiceImproved, self).action_invoice_open()

        if self.type == 'out_invoice':
            #Method that return the mail form.
            return self.action_invoice_sent()
        return res
