# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _

class SignatureRequestItem(models.Model):
    _inherit = 'signature.request.item'

    hr_applicant_id = fields.Many2one('hr.applicant', string="Applicant")
