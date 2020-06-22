# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _

class SignatureRequest(models.Model):
	_inherit = 'signature.request'

	data_agreement_document = fields.Boolean(related='template_id.data_agreement_document')