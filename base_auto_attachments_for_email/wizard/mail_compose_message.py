# -*- coding: utf-8 -*-
##############################################################################
#
#     This file is part of mail_attach_existing_attachment,
#     an Odoo module.
#
#     Copyright (c) 2015 ACSONE SA/NV (<http://acsone.eu>)
#
#     mail_attach_existing_attachment is free software:
#     you can redistribute it and/or modify it under the terms of the GNU
#     Affero General Public License as published by the Free Software
#     Foundation,either version 3 of the License, or (at your option) any
#     later version.
#
#     mail_attach_existing_attachment is distributed
#     in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
#     even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#     PURPOSE.  See the GNU Affero General Public License for more details.
#
#     You should have received a copy of the GNU Affero General Public License
#     along with mail_attach_existing_attachment.
#     If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api
import logging


_logger = logging.getLogger(__name__)

class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def getCompanyAttachments(self, template_id, partner_id, company_id):
        domain = [('mail_template_ids', '=', template_id)]

        attachments = []
        # Check here if partner should receive the docs
        if not partner_id.send_attachments or (partner_id.parent_id and not partner_id.parent_id.send_attachments):
            return attachments

        # Language
        if partner_id:
            domain.append(('|'))
            domain.append(('lang_id.code', '=', str(partner_id.lang)))
            domain.append(('lang_id', '=', False))

        # Company
        if company_id:
            domain.append(('company_id', '=', company_id.id))

        attachment_settings = self.env['res.company.attachment'].search(domain)
        for setting in attachment_settings:
            for attachment in setting.attachments_ids:
                attachments.append(attachment.id)
        return attachments

    @api.multi
    def onchange_template_id(self, template_id, composition_mode, model, res_id):
        values = super(MailComposeMessage, self).onchange_template_id(template_id, composition_mode, model, res_id)

        if template_id:
            # Check here if partner should receive the docs
            company_id = False
            partner_id = False
            data = self.env[model].search([('id', '=', res_id)])
            if data.fields_get('company_id'):
                company_id = data.company_id
            if data.fields_get('partner_id'):
                partner_id = data.partner_id

            already_attached = []
            if 'attachment_ids' in values['value']:
                already_attached = values['value']['attachment_ids'][0][2]
            already_attached += self.getCompanyAttachments(template_id, partner_id, company_id)
            values['value'].setdefault('attachment_ids', list()).append(already_attached)
        return values
