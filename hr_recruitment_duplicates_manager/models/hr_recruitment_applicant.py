# -*- coding: utf-8 -*-
from odoo import models, fields, api

import logging
_logger = logging.getLogger(__name__)


class HrRecruitmentApplicant(models.Model):
    _inherit = 'hr.applicant'

    suspect_ids = fields.One2many('hr_duplicate_suspect', 'origin_id', string="Suspected duplicates", ondelete='cascade')
    suspect_ids_count = fields.Integer(string="Number of suspected applications", compute='_compute_suspect_ids_count')

    @api.multi
    def _compute_suspect_ids_count(self):
        for applicant in self:
            applicant.suspect_ids_count = len(applicant.suspect_ids)

    @api.model
    def create(self, vals):
        res = super(HrRecruitmentApplicant, self).create(vals)
        self._search_duplicates(res)
        return res

    @api.multi
    def write(self, vals):
        for record in self:
            result = super(HrRecruitmentApplicant, record).write(vals)
            record._search_duplicates(record)
            return result

    @api.model
    def _action_check_duplicates(self):
        for applicant in self:
            self._search_duplicates(applicant)

    @api.multi
    def _search_duplicates(self, vals):
        # Delete already created lines
        _logger.info("\n\n Valeurs")
        _logger.info(vals)
        for suspect_rec in vals.suspect_ids:
            suspect_rec.unlink()

        # Search for suspected duplicates
        domain = [
            ('id', '!=', vals.id),
            '|',
                ('name', '=ilike', vals.name),
                ('partner_name', '=ilike', vals.partner_name)]
        if vals.email_from and vals.partner_mobile:
            domain = [
                ('id', '!=', vals.id),
                '|',
                    '|',
                        ('name', '=ilike', vals.name),
                        ('partner_name', '=ilike', vals.partner_name),
                    '|',
                        ('email_from', '=', vals.email_from),
                        ('partner_mobile', '=', vals.partner_mobile)
            ]

        corresponding_records = self.env['hr.applicant'].search(domain)

        # Create link lines for suspected duplicates
        for rec in corresponding_records:
            self.env['hr_duplicate_suspect'].create({
                'duplicate_id': rec.id,
                'origin_id': vals.id
            })
