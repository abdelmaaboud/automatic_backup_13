from odoo import models, fields, api

import datetime
import logging
_logger = logging.getLogger(__name__)


class mail_message_improved(models.Model):
    _inherit = 'mail.message'

    @api.model
    def _get_related(self):
        if not self.model:
            return False
        return self.env[self.model].search([('id', '=', self.res_id)])

    @api.model
    def get_project_name(self):
        related = self._get_related()

        # Check if related is kind of Task or Issue
        if related and self.model in ['project.task']:
            if related.project_id:
                return related.project_id.name
        return False

    @api.model
    def get_partner_name(self):
        related = self._get_related()

        # Check if related model has "partner_id" as field
        field_ids = self.env['ir.model.fields'].search([('model_id', '=', self.model)])
        if related:
            for field in field_ids:
                if field.name == 'partner_id':
                    if related.partner_id.name:
                        return related.partner_id.display_name
        return False
