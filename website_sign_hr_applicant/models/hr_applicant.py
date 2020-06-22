# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _

class HRApplicant(models.Model):
    _inherit = 'hr.applicant'

    signature_request_ids = fields.One2many('signature.request.item', 'hr_applicant_id', string='Sign Documents')
    signature_request_count = fields.Integer(compute='_compute_signature_request_count')
    has_signed_main_data_document = fields.Boolean(compute='_compute_has_signed_main_data_document', store=True, default=False)

    @api.one
    def _compute_signature_request_count(self):
        self.signature_request_count = len(self.signature_request_ids)

    @api.one
    @api.depends('signature_request_ids.state')
    def _compute_has_signed_main_data_document(self):
        for doc in self.signature_request_ids:
            if doc.signature_request_id.data_agreement_document and doc.state == 'completed':
                self.has_signed_main_data_document = True
                return
        self.has_signed_main_data_document = False

    @api.multi
    def action_signed_documents(self):
        self.ensure_one()

        res = self.env['ir.actions.act_window'].for_xml_id('website_sign_hr_applicant', 'action_signed_documents')
        res['context'] = {
            'default_hr_applicant_id': self.id
        }
        return res
