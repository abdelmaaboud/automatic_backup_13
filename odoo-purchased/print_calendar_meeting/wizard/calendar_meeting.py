# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import Warning

import logging
_logger = logging.getLogger(__name__)

class CalendarMeeting(models.TransientModel):
    _name = 'calendar.meeting.report'

    start_date = fields.Date(string='Meeting Start Date', required=True, default=fields.date.today())
    end_date = fields.Date(string='Meeting End Date', required=True, default=fields.date.today())
    attendees_ids = fields.Many2many('res.partner', string='Select Attendees')

    @api.multi
    def print_meeting_report(self):
        meet_ids = []
        if not self.attendees_ids:
            attendee = self.env['res.partner'].search([]).ids
        else:
            attendee = self.attendees_ids.ids
        data = self.read()[0]
        
        self.env.cr.execute("select DISTINCT ce.id, CASE \
                              WHEN ce.allday THEN ce.start_date\
                              ELSE ce.start_datetime\
                           END  AS start_datetime FROM calendar_event ce left join calendar_event_res_partner_rel at on at.calendar_event_id = ce.id WHERE (ce.start_date >= %s OR ce.start_datetime >= %s) AND (ce.stop_date <= %s OR ce.stop_datetime <= %s) AND (at.res_partner_id IN %s) ORDER BY start_datetime",(self.start_date, self.start_date, self.end_date, self.end_date, tuple(attendee)))

        res = self.env.cr.fetchall()

        if res:
            meet_ids = [x[0] for x in res]
        if not meet_ids:
            raise Warning (_('No meetings found'))
        datas = {'ids': meet_ids}
        datas.update(model='calendar.event')
        datas.update({'form': data})
#         act = self.env['report'].get_action(self, 'print_calendar_meeting.calendar_meeting_report_id', data=datas)
        act = self.env.ref('print_calendar_meeting.calendar_meeting_report').report_action(self, data=datas, config=False)
        return act

#vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: