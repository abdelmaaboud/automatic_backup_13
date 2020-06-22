# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _

class SignatureRequestTemplate(models.Model):
	_inherit = 'signature.request.template'

	data_agreement_document = fields.Boolean(default=False)