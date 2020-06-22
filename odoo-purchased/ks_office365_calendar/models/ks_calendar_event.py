from odoo import models, fields, api, _
from odoo.addons.calendar.models.calendar import get_real_ids


class KsOdooCalendar(models.Model):
    _inherit = 'calendar.event'

    ks_office_event_id = fields.Char("Event ID", default="")
    ks_user_id = fields.Many2one('res.users', default=False)
    ks_is_updated = fields.Boolean(default=True)
    ks_rec_type_noend = fields.Boolean(default=False)

    @api.multi
    def write(self, values):
        res = super(KsOdooCalendar, self).write(values)

        # To keep track of any event being updated, if not don't sync
        if 'ks_is_updated' not in values:
            for rec in self:
                rec.ks_is_updated = True

        if 'attendee_ids' in values or 'partner_ids' in values or 'start_date' in values or 'stop_date' in values or \
                'allday' in values or 'interval' in values or 'rrule_type' in values or 'end_type' in values or \
                'final_date' in values or 'count' in values:
            ks_office_settings = self.sudo().env['ks_office365.settings'].search([], limit=1)
            if not ks_office_settings.ks_dont_sync:
                ks_sync_individual = ks_office_settings.ks_sync_individual
                if ks_sync_individual:
                    res_user = self.sudo().env['res.users'].search([('id', '=', self.env.user.id)])
                    return res_user.ks_post_events(q_context=None, ks_individual_event=self)
        return res

    @api.multi
    def unlink(self, can_be_deleted=True):
        # Keeping track of the events that are deleted from odoo calendar
        real_events = self.env['calendar.event'].browse(set(get_real_ids(self.ids)))
        for event in real_events:
            if self.env.user.ks_sync_deleted_event:
                self.env['ks.deleted'].create({
                    'name': event.name,
                    'ks_odoo_id': event.id,
                    'ks_office_id': event.ks_office_event_id,
                    'ks_module': 'calendar',
                    'ks_user_id': self.env.user.id,
                })
        return super(KsOdooCalendar, self).unlink(can_be_deleted)

