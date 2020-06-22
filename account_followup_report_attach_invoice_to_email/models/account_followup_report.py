# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, exceptions
from odoo.tools import append_content_to_html, DEFAULT_SERVER_DATE_FORMAT
import time
from odoo.tools.mail import html2plaintext

import base64
import json
import logging
_logger = logging.getLogger(__name__)


class AccountReportFollowupManager(models.Model):
    _inherit = 'account.report.manager'

    summary_bottom = fields.Char()


class AccountFollowUpReport(models.AbstractModel):
    _inherit = 'account.followup.report'

    def get_default_summary(self, options):
        res = super(AccountFollowUpReport, self).get_default_summary(options)
        followup_line = self.get_followup_line(options)
        partner = self.env['res.partner'].browse(options.get('partner_id'))
        lang = partner.lang or self.env.user.lang or 'en_US'
        summary_bottom = ''
        subject = 'Account Customer Statement'
        if followup_line:
            summary_bottom = followup_line.with_context(lang=lang).description_bottom or ''
            signature = followup_line.with_context(lang=lang).signature or 'Accounting Team'
            subject = followup_line.with_context(lang=lang).subject
            try:
                summary_bottom = summary_bottom % {'partner_name': partner.name,
                                                   'date': time.strftime('%Y-%m-%d'),
                                                   'user_signature': html2plaintext(self.env.user.signature or ''),
                                                   'company_name': self.env.user.company_id.name}
            except ValueError as e:
                message = "An error has occurred while formatting your followup letter/email (bottom). (Lang: %s, Followup Level: #%s) \n\nFull error description: %s" \
                          % (partner.lang, followup_line.id, e)
                raise ValueError(message)
        else:
            summary_bottom =  self.env.user.company_id.with_context(lang=lang).overdue_msg or \
                   self.env['res.company'].with_context(lang=lang).default_get(['overdue_msg'])['overdue_msg']
            signature = 'Accounting Team'
        options['summary_bottom'] = summary_bottom
        options['signature'] = signature
        options['subject'] = subject
        return res

    def get_pdf(self, options, minimal_layout=True):
        return super(AccountFollowUpReport, self.with_context(force_portrait=True)).get_pdf(options, minimal_layout)

    def print_followup(self, options, params):
        partner_id = params.get('partner')
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            partner.message_post(body=_('Follow-up letter printed'), subtype='account_reports.followup_logged_action', message_type="notification")
        options['partner_id'] = str(partner_id)
        followup_line = self.get_followup_line(options)
        options['partner_id'] = partner_id
        subject = 'Account Customer Statement'
        if followup_line:
            lang = partner.lang or self.env.user.lang or 'en_US'
            summary_bottom = followup_line.with_context(lang=lang).description_bottom or ''
            signature = followup_line.with_context(lang=lang).signature or 'Accounting Team'
            subject = followup_line.with_context(lang=lang).subject
            try:
                summary_bottom = summary_bottom % {'partner_name': partner.name,
                                                   'date': time.strftime('%Y-%m-%d'),
                                                   'user_signature': html2plaintext(self.env.user.signature or ''),
                                                   'company_name': self.env.user.company_id.name}
            except ValueError as e:
                message = "An error has occurred while formatting your followup letter/email (bottom). (Lang: %s, Followup Level: #%s) \n\nFull error description: %s" \
                          % (partner.lang, followup_line.id, e)
                raise ValueError(message)
                
            options['summary_bottom'] = summary_bottom
            options['signature'] = signature
            options['subject'] = subject
        return {
                'type': 'ir_actions_account_report_download',
                'data': {'model': 'account.followup.report',
                         'options': json.dumps(options),
                         'output_format': 'pdf',
                         }
                }
    
    @api.model
    def send_email(self, options):
        if options and "partner_id" in options:
            partner_id = self.env['res.partner'].browse(options.get('partner_id'))
            email = self.env['res.partner'].browse(partner_id.address_get(['invoice'])['invoice']).email
            if email and email.strip():
                # Get report lines, containing invoice number
                lines = self.env['account.followup.report'].with_context(lang=partner_id.lang, public=True).get_lines(options)
                invoice_ids = self.env['account.invoice']
                for line in lines:
                    if 'has_invoice' in line and line['has_invoice']:
                        aml = self.env['account.move.line'].browse(line['id'])
                        if aml and aml.invoice_id:
                            invoice_ids |= aml.invoice_id


                #Get all invoices related to numbers then browse it.
                for invoice in invoice_ids:
                    # Create ir.attachment and PDF for invoice when it doesn't exists
                    pdf = self.env.ref('account.account_invoices').sudo().render_qweb_pdf([invoice.id])[0]
                attachments = self.env['ir.attachment'].search([('res_id', 'in', invoice_ids.ids), ('res_model', '=', "account.invoice")]).ids
                
                
                subject = 'Account Customer Statement'
                followup_line = False
                if options and 'partner_followup_level' in options and options.get('partner_followup_level') and options.get('partner_followup_level')[str(partner_id.id)]:
                    followup_line = options.get('partner_followup_level')[str(partner_id.id)][0]
                    if followup_line:
                        followup_line = self.env['account_followup.followup.line'].browse(followup_line)
                        lang = partner_id.lang or self.env.user.lang or 'en_US'
                        summary_bottom = followup_line.with_context(lang=lang).description_bottom or ''
                        signature = followup_line.with_context(lang=lang).signature or 'Accounting Team'
                        subject = followup_line.with_context(lang=lang).subject
                        try:
                            summary_bottom = summary_bottom % {'partner_name': partner_id.name,
                                                               'date': time.strftime('%Y-%m-%d'),
                                                               'user_signature': html2plaintext(self.env.user.signature or ''),
                                                               'company_name': self.env.user.company_id.name}
                        except ValueError as e:
                            message = "An error has occurred while formatting your followup letter/email (bottom). (Lang: %s, Followup Level: #%s) \n\nFull error description: %s" \
                                      % (partner_id.lang, followup_line.id, e)
                            raise ValueError(message)

                        options['summary_bottom'] = summary_bottom
                        options['signature'] = signature
                        options['subject'] = subject

                body = self.with_context(print_mode=True, mail=True, keep_summary=True).get_html(options)
                # Attach to all related PDF to email
                mail = self.env['mail.mail'].create({
                    'subject': _('%s - Payment Reminder') % self.env.user.company_id.name if not followup_line or not followup_line.subject else followup_line.subject,
                    'body_html': body,
                    'email_from': self.env.user.email or '',
                    'email_to': email,
                    'attachment_ids': [(6, 0, attachments)]
                })
                msg = _(': Sent a followup email to %s\n%s' % (email, body.decode('utf-8')))
                partner_id.message_post(body=msg, subtype='account_reports.followup_logged_action', message_type="notification")
                return True
            else:
                raise exceptions.Warning(_('Could not send mail to partner because it does not have any email address defined'))
        return False
