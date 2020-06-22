# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
from odoo import models, fields, api, _, exceptions
import logging

_logger = logging.getLogger(__name__)


class HRApplicant(models.Model):
    _inherit = 'hr.applicant'

    @api.multi
    def action_open_wizard(self):
        if len(self) <= 1:
            raise exceptions.Warning(_("You must select at least two similar applicants to merge them!"))
        is_mergeable = True
        for i, applicant in enumerate(self):
            if i == 0:
                continue
            if not self._compare_applicants(self[i - 1], applicant):
                is_mergeable = False
                break

        # partner_names = list(dict.fromkeys([i.lower().strip() for i in self.mapped('partner_name') if i]))
        # email_from = list(dict.fromkeys([i.lower().strip() for i in self.mapped('email_from') if i]))
        if not is_mergeable:
            raise exceptions.Warning(
                _("The partner name, the phone number and the email from applicants you want to merge must be the same if set!"))
        return {
            'type': 'ir.actions.act_window',
            'name': 'Merge Applicants',
            'res_model': 'merge.applicant.wizard',
            'view_mode': 'form',
            'target': 'new',
            'view_type': 'form',
            'context': {'default_applicant_ids': self.env.context.get('active_ids', False)},
        }

    def _compare_applicants(self, applicant_1, applicant_2):
        partner_name_1, phone_1, mobile_1, email_1 = self._sanitize(applicant_1)
        partner_name_2, phone_2, mobile_2, email_2 = self._sanitize(applicant_2)
        return partner_name_1 and partner_name_2 and partner_name_1 == partner_name_2 \
                and ((not phone_1 and not mobile_1) or
                    (not phone_2 and not mobile_2) or
                    (phone_1 and phone_2 and phone_1 == phone_2) or
                    (mobile_1 and mobile_2 and mobile_1 == mobile_2) or
                    (phone_1 and mobile_2 and phone_1 == mobile_2) or
                    (mobile_1 and phone_2 and mobile_1 == phone_2)) and \
                    (not email_1 or not email_2 or email_1 == email_2)


    def _sanitize(self, applicant):
        if not applicant:
            raise exceptions.ValidationError(_("There is a problem with selected applicants!"))
        else:
            return self._sanitize_name(applicant.partner_name),\
                   self._sanitize_phone(applicant.partner_phone),\
                   self._sanitize_phone(applicant.partner_mobile),\
                   self._sanitize_email(applicant.email_from)

    def _sanitize_name(self, name):
        if name:
            name = [i for i in name.lower().strip().split(' ') if i]
            name.sort()
        return name

    def _sanitize_email(self, email):
        if email:
            email = email.lower().strip()
        return email

    def _sanitize_phone(self, phone):
        if phone:
            phone = phone.replace('+', '00')
        return phone
