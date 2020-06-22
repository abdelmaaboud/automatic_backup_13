
# -*- coding: utf-8 -*-

import time
from openerp import api, fields, models

import logging
_logger = logging.getLogger(__name__)

class ReportCalendarMeetingReport(models.AbstractModel):
    _name = 'report.print_calendar_meeting.calendar_meeting_report_id'

    @api.model
    def get_report_values(self, docids, data=None):
        meeting_ids = data['ids']
        start = data['form']['start_date']
        stop = data['form']['end_date']
        attendee_ids = data['form']['attendees_ids']
        attendee = ''
        for att in attendee_ids:
            ats = self.env['res.partner'].browse(att)
            attendee += ats.name + ', '
        docargs = {
            'doc_ids': meeting_ids,
            'doc_model': 'calendar.event',
            'docs': self.env['calendar.event'].browse(meeting_ids),
            'start_date': start,
            'end_date': stop,
            'user_id': self.env.user.name,
            'attendee': attendee,
            'data': data
        }
#         return self.env['report'].render(\
#         'print_calendar_meeting.calendar_meeting_report_id', values=docargs)
        return self.env.ref('print_calendar_meeting.calendar_meeting_report').report_action(self, data=docargs, config=False)   # odoo 11


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
