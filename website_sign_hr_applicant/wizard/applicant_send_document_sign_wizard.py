# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models, _
_logger = logging.getLogger(__name__)


class HRApplicantSendDocumentSignWizard(models.TransientModel):
    """ Main wizard class """
    _name = 'applicant.send.document.sign.wizard'
    _description = 'Applicant Send Document Wizard'

    applicant_id = fields.Many2one('hr.applicant', required=True)
    email = fields.Char(required=True)
    signature_request_template_id = fields.Many2one('signature.request.template', 'Template', required=True)
    subject = fields.Char(required=True)
    message = fields.Text(required=True)

    @api.model
    def default_get(self, fields):
        res = super(HRApplicantSendDocumentSignWizard, self).default_get(fields)
        if not res.get('default_applicant_id') and self.env.context.get('active_id') and self.env.context.get('active_model') == 'hr.applicant':
            applicant = self.env['hr.applicant'].search([('id', '=', self.env.context['active_id'])], limit=1)
        elif res.get('default_applicant_id') and self.env.context.get('active_model') == 'hr.applicant':
            applicant = self.env['hr.applicant'].browse(self.env.context['default_applicant_id'], limit=1)

        res['applicant_id'] = applicant.id
        res['email'] = applicant.email_from

        return res

    @api.multi
    def send_document(self):
        self.ensure_one()
        data = {}
        data['form'] = self.read(['signature_request_template_id', 'subject', 'message'])[0]

        # Reference
        ref = self.applicant_id.partner_name if self.applicant_id.partner_name != "" else self.applicant_id.name
        ref = (ref + " " + self.signature_request_template_id.display_name) if ref else self.signature_request_template_id.display_name

        # Check if partner exists
        partner = None
        if len(self.applicant_id.partner_id) == 0:
            partner = self.env['res.partner'].create({
                'name': self.applicant_id.partner_name,
                'email': self.applicant_id.email_from,
                'phone': self.applicant_id.partner_phone,
                'mobile': self.applicant_id.partner_mobile,
            })
            self.applicant_id.partner_id = partner
        else:
            partner = self.applicant_id.partner_id

        # Role
        role = self.env['signature.item.party'].search([('name', '=', 'Customer')])

        # Signers
        signers = []
        signers.append({
            'partner_id': partner.id,
            'role': role.id,
        })
        
        # Create the request
        request = self.env['signature.request'].create({
            'template_id': self.signature_request_template_id.id,
            'reference': ref,
        })

        # Create the signer
        signer = self.env['signature.request.item'].create({
            'signature_request_id': request.id,
            'hr_applicant_id': self.applicant_id.id,
            'partner_id': partner.id,
            'signer_email': self.email,
            'role_id': role.id,
        })

        # Send the request
        request.action_sent(self.subject, self.message)
