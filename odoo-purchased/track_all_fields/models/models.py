# -*- coding: utf-8 -*-

from odoo import api, models, fields

class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    @api.model
    def _get_tracked_fields(self, updated_fields):
        super(MailThread, self)._get_tracked_fields(updated_fields)
        tracked_fields = []
        Model = self.env['ir.model']
        if Model.search([('model', '=', str(self._name))]).track_all_fields:
            for name, field in self._fields.items():
                if name not in ['write_date', '__last_update']:
                    tracked_fields.append(name)
        else:
            for name, field in self._fields.items():
                if getattr(field, 'track_visibility', False):
                    tracked_fields.append(name)

        if tracked_fields:
            return self.fields_get(tracked_fields)
        return {}


class IrModel(models.Model):
    _inherit = 'ir.model'

    track_all_fields = fields.Boolean(string="Track all fields")
