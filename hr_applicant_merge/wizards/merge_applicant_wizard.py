# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
from odoo import models, fields, api, _, exceptions
import logging

_logger = logging.getLogger(__name__)


class HRApplicant(models.TransientModel):
    _name = 'merge.applicant.wizard'

    applicant_ids = fields.Many2many('hr.applicant', string="Applicants")
    type = fields.Selection([('to_selected', _('Merge to selected applicant and archive others')),
                             ('to_selected_unlink', _('Merge to selected applicant and delete others')),
                             ('new', _('Create a new applicant and archive old ones')),
                             ('new_unlink', _('Create a new applicant and delete old ones'))], default='to_selected')
    applicant_id = fields.Many2one('hr.applicant')

    def action_merge_applicants(self):
        if 'to_selected' in self.type:
            if not self.applicant_id:
                raise exceptions.Warning(_("You must select an applicant to merge."))
            for applicant_id in self.applicant_ids:
                if applicant_id == self.applicant_id:
                    continue
                if applicant_id.attachment_ids.exists():
                    applicant_id.attachment_ids.sudo().write({'res_id': self.applicant_id.id})
                if '_unlink' in self.type:
                    applicant_id.sudo().unlink()
                else:
                    applicant_id.sudo().write({'active': False})
        elif 'new' in self.type:
            name = list(dict.fromkeys([i.strip() for i in self.applicant_ids.mapped('name') if i]))
            partner_name = list(dict.fromkeys([i.strip() for i in self.applicant_ids.mapped('partner_name') if i]))
            categ_ids = list(dict.fromkeys([i.ids for i in self.applicant_ids.mapped('categ_ids') if i]))
            email_from = list(dict.fromkeys([i.strip() for i in self.applicant_ids.mapped('email_from') if i]))
            partner_id = list(dict.fromkeys([i.id for i in self.applicant_ids.mapped('partner_id') if i]))
            partner_phone = list(dict.fromkeys([i.strip() for i in self.applicant_ids.mapped('partner_phone') if i]))
            partner_mobile = list(dict.fromkeys([i.strip() for i in self.applicant_ids.mapped('partner_mobile') if i]))
            type_id = list(dict.fromkeys([i.id for i in self.applicant_ids.mapped('type_id') if i]))
            job_id = list(dict.fromkeys([i.id for i in self.applicant_ids.mapped('job_id') if i]))
            department_id = list(dict.fromkeys([i.id for i in self.applicant_ids.mapped('department_id') if i]))
            company_id = list(dict.fromkeys([i.id for i in self.applicant_ids.mapped('company_id') if i]))
            user_id = list(dict.fromkeys([i.id for i in self.applicant_ids.mapped('user_id') if i]))
            priority = list(dict.fromkeys([i for i in self.applicant_ids.mapped('priority') if i]))
            medium_id = list(dict.fromkeys([i.id for i in self.applicant_ids.mapped('medium_id') if i]))
            source_id = list(dict.fromkeys([i.id for i in self.applicant_ids.mapped('source_id') if i]))
            reference = list(dict.fromkeys([i.strip() for i in self.applicant_ids.mapped('reference') if i]))
            salary_expected = list(dict.fromkeys([i for i in self.applicant_ids.mapped('salary_expected') if i]))
            salary_proposed = list(dict.fromkeys([i for i in self.applicant_ids.mapped('salary_proposed') if i]))
            availability = list(dict.fromkeys([i for i in self.applicant_ids.mapped('availability') if i]))
            description = list(dict.fromkeys([i.strip() for i in self.applicant_ids.mapped('description') if i]))
            if name and partner_name and email_from:
                res = self.env['hr.applicant'].sudo().create({
                    'name': name[0],
                    'partner_name': partner_name[0],
                    'categ_ids': categ_ids if categ_ids else False,
                    'email_from': email_from[0],
                    'partner_id': partner_id if partner_id else False,
                    'partner_phone': partner_phone[0] if partner_phone else False,
                    'partner_mobile': partner_mobile[0] if partner_mobile else False,
                    'type_id': type_id[0] if type_id else False,
                    'job_id': job_id[0] if job_id else False,
                    'department_id': department_id[0] if department_id else False,
                    'company_id': company_id[0] if company_id else False,
                    'user_id': user_id[0] if user_id else False,
                    'priority': priority[0] if priority else False,
                    'medium_id': medium_id[0] if medium_id else False,
                    'source_id': source_id[0] if source_id else False,
                    'reference': reference[0] if reference else False,
                    'salary_expected': salary_expected[0] if salary_expected else False,
                    'salary_proposed': salary_proposed[0] if salary_proposed else False,
                    'availability': availability[0] if availability else False,
                    'description': description[0] if description else False,
                })
                self.applicant_ids.mapped('attachment_ids').write({'res_id': res.id})
            else:
                raise exceptions.Warning(_(
                    "To create a new applicant, you must have at least one application's name, one name and one email."))

            if '_unlink' in self.type:
                self.applicant_ids.sudo().unlink()
            else:
                self.applicant_ids.sudo().write({'active': False})
        return {}
