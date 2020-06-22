# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)


class HrDuplicateSuspects(models.Model):
    _name = 'hr_duplicate_suspect'

    origin_id = fields.Many2one('hr.applicant', string="New applicant", ondelete='cascade')
    duplicate_id = fields.Many2one('hr.applicant', string="Duplicate", ondelete='cascade', readonly=True)

    origin_partner_name = fields.Char(related='origin_id.partner_name')
    origin_job_id = fields.Many2one(related='origin_id.job_id')
    origin_stage_id = fields.Many2one(related='origin_id.stage_id')
    origin_create_date = fields.Datetime(related='origin_id.create_date')

    duplicate_name = fields.Char(related='duplicate_id.name')
    duplicate_partner_name = fields.Char(related='duplicate_id.partner_name')
    duplicate_job_id = fields.Many2one(related='duplicate_id.job_id')
    duplicate_stage_id = fields.Many2one(related='duplicate_id.stage_id')
    duplicate_create_date = fields.Datetime(related='duplicate_id.create_date')

    @api.multi
    def name_get(self):
        result = []
        for suspect in self:
            result.append((suspect.id, _("Duplicate Suspect from %s") % suspect.origin_id.name))
        return result
