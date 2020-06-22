from odoo import models, fields, api, _
import requests
import json
from datetime import datetime, timedelta, MAXYEAR
from dateutil import tz
from dateutil.relativedelta import relativedelta
from odoo.addons.calendar.models.calendar import get_real_ids


class KsOffice365Calendar(models.Model):
    _inherit = "res.users"

    ks_import_office_calendar = fields.Boolean("Import", default=True, readonly=True)
    ks_export_office_calendar = fields.Boolean("Export", default=True, readonly=True)
    ks_calendar_sync_using_subject = fields.Boolean("Subject", default=True, readonly=True)
    ks_calendar_sync_using_start_datetime = fields.Boolean("Start DateTime", default=True)
    ks_calendar_sync_using_end_datetime = fields.Boolean("End DateTime", default=True)
    ks_calendar_sync_days_before = fields.Integer(string="Sync events from last (in days)", default=1,
                                                  help="This will allow you to sync only those events/meetings that are "
                                                       "created or updated in the given days. Here 0 days means Today.")
    ks_calendar_sync_using_days = fields.Boolean(default=True)
    ks_calendar_filter_domain = fields.Char("Filter Domain", help="This filter domain is only applicable while syncing "
                                                                  "from Odoo to office 365.")
    ks_sync_deleted_event = fields.Boolean("Sync deleted events", default=True)

    def ks_get_events(self):
        try:
            if self.ks_calendar_sync_using_days:
                _days = str(self.ks_calendar_sync_days_before)
                if not (_days.isdigit() and not len(_days) > 3) or int(_days) < 0:
                    return self.ks_show_error_message(_("Days can only be in numbers less then 999 and greater "
                                                        "than or equal to 0."))
            res = self.ks_import_events()
            return res
        except Exception as ex:
            if type(ex) is requests.exceptions.ConnectionError:
                ex = "Internet Connection Failed"
            ks_current_job = self.env["ks.office.job"].search([('ks_records', '>=', 0),
                                                               ('ks_status', '=', 'in_process'),
                                                               ('ks_job', '=', 'calendar_import'),
                                                               ('create_uid', '=', self.env.user.id)])
            if ks_current_job:
                ks_current_job.write({'ks_status': 'error', 'ks_error_text': ex})
                self.env.cr.commit()
            self.ks_create_log("calendar", "Error", "", 0, datetime.today(), "office_to_odoo", False, "failed",
                               _(str(ex) + "\nCheck Jobs to know how many records have been processed."))
            return self.ks_has_sync_error()

    def ks_import_events(self):
        ks_current_job = self.ks_is_job_completed("calendar_import", "calendar")
        if not ks_current_job:
            return self.ks_show_error_message(_('Process Is Already Running.'))
        else:
            ks_current_job.write({'ks_status': 'in_process', 'ks_error_text': False})

        ks_current_datatime = datetime.today()
        ks_sync_calendar_from_date = str(datetime.min.replace(year=1900)).replace(' ', 'T') + ".0000000"
        if self.ks_calendar_sync_using_days:
            ks_days = self.ks_calendar_sync_days_before
            ks_sync_calendar_from_date = ks_current_datatime + relativedelta(days=-ks_days)

        ks_events_imported = ks_current_job.ks_records
        ks_api_endpoint = "https://graph.microsoft.com/v1.0/me/events?$top=1000000&$skip=" + str(ks_events_imported)
        ks_api_endpoint += "&$filter=lastModifiedDateTime ge " + str(ks_sync_calendar_from_date).replace(' ', 'T') + "Z"

        ks_auth_token = self.ks_auth_token
        if not ks_auth_token:
            self.ks_create_log("calendar", "", "", 0, ks_current_datatime, "office_to_odoo", "authentication",
                               "failed", _("Generate Authentication Token"))
            ks_current_job.write({'ks_status': 'completed'})
            return self.ks_show_error_message(_('Generate Authentication Token!'))

        ks_head = {
            "Authorization": ks_auth_token,
            "Host": "graph.microsoft.com"
        }
        ks_response = requests.get(ks_api_endpoint, headers=ks_head)
        ks_json_data = json.loads(ks_response.text)

        # For finding the duplicates
        ks_all_response = requests.get("https://graph.microsoft.com/v1.0/me/events?$top=1000000", headers=ks_head)

        if 'error' in ks_json_data:
            if ks_json_data["error"]['code'] == 'InvalidAuthenticationToken':
                self.refresh_token()
                ks_head['Authorization'] = self.ks_auth_token
                ks_response = requests.get(ks_api_endpoint, headers=ks_head)
                ks_json_data = json.loads(ks_response.text)
                ks_all_response = requests.get("https://graph.microsoft.com/v1.0/me/events?$top=1000000",
                                               headers=ks_head)
                ks_json_all_data = json.loads(ks_all_response.text)
                if 'error' in ks_json_data or 'error' in ks_json_all_data:
                    self.ks_create_log("authentication", "Authentication", "", 0, ks_current_datatime,
                                       "office_to_odoo", "authentication", "failed",
                                       _(ks_json_data["error"]['code']))
                    ks_current_job.write({'ks_status': 'completed'})
                    return self.ks_show_error_message(
                        _("Some error occurred! \nPlease check logs for more information."))
            else:
                self.ks_create_log("authentication", "Authentication", "", 0, ks_current_datatime,
                                   "office_to_odoo", "authentication", "failed",
                                   _(ks_json_data["error"]['code']))
                ks_current_job.write({'ks_status': 'completed'})
                return self.ks_show_error_message(
                    _("Some error occurred! \nPlease check logs for more information."))

        ks_syncing_field = list()
        if self.ks_calendar_sync_using_subject:
            ks_syncing_field.append("subject")
        if self.ks_calendar_sync_using_start_datetime:
            ks_syncing_field.append("start")
        if self.ks_calendar_sync_using_end_datetime:
            ks_syncing_field.append("end")

        ks_office_events = json.loads(ks_response.text)['value']
        ks_all_office_events = json.loads(ks_all_response.text)['value']
        ks_all_real_ids = set(get_real_ids(self.env['calendar.event'].search([]).ids))
        ks_existing_odoo_events = self.env['calendar.event'].browse(list(ks_all_real_ids))

        # Finding duplicates
        ks_office_duplicate_subject = set()
        ks_office_duplicate_subject_start = set()
        ks_office_duplicate_subject_end = set()
        ks_office_duplicate_subject_start_end = set()
        if 'subject' in ks_syncing_field and 'start' not in ks_syncing_field and 'end' not in ks_syncing_field:
            # Finding duplicates in office 365
            _subject = list()
            for ks_event in ks_all_office_events:
                if _subject.count(ks_event['subject']) == 1:
                    self.ks_create_log("calendar", ks_event['subject'], ks_event['id'], 0,
                                       ks_current_datatime, "office_to_odoo", False, "failed",
                                       _("Multiple event with the same subject \'" + ks_event['subject'] +
                                         "\' exists in in Office 365.\nNote: This event is being synced with respect to "
                                         "subject."))
                    ks_office_duplicate_subject.add(ks_event['subject'])
                _subject.append(ks_event['subject'])

        elif 'subject' in ks_syncing_field and 'start' in ks_syncing_field and 'end' not in ks_syncing_field:
            # Finding duplicates in office
            _subject_start = list()
            for ks_event in ks_all_office_events:
                _start = datetime.strptime(ks_event['start']['dateTime'].split('.')[0].replace('T', ' '),
                                           '%Y-%m-%d %H:%M:%S')
                if _subject_start.count((ks_event['subject'], ks_event['start']['dateTime'])) == 1:
                    self.ks_create_log("calendar", ks_event['subject'], ks_event['id'], 0, ks_current_datatime,
                                       "office_to_odoo", False, "failed",
                                       _("Multiple event with the same subject \'" + ks_event['subject'] +
                                         "\' and start datetime \'" + str(_start) +
                                         "\' exists in in Office 365.\nNote: This event is being synced with respect to "
                                         "subject and start datetime."))
                    ks_office_duplicate_subject_start.add((ks_event['subject'], _start))
                _subject_start.append((ks_event['subject'], ks_event['start']['dateTime']))

        elif 'subject' in ks_syncing_field and 'end' in ks_syncing_field and 'start' not in ks_syncing_field:
            # Finding duplicates in office
            _subject_end = list()
            for ks_event in ks_all_office_events:
                _end = datetime.strptime(ks_event['end']['dateTime'].split('.')[0].replace('T', ' '),
                                         '%Y-%m-%d %H:%M:%S')
                if _subject_end.count((ks_event['subject'], ks_event['end']['dateTime'])) == 1:
                    self.ks_create_log("calendar", ks_event['subject'], ks_event['id'], 0,
                                       ks_current_datatime, "office_to_odoo", False, "failed",
                                       _("Multiple event with the same subject \'" + ks_event['subject'] +
                                         "\' and end datetime \'" + str(_end) +
                                         "\' exists in in Office 365.\nNote: This event is being synced with respect to "
                                         "subject and end datetime."))
                    ks_office_duplicate_subject_end.add((ks_event['subject'], str(_end)))
                _subject_end.append((ks_event['subject'], ks_event['end']['dateTime']))

        elif 'subject' in ks_syncing_field and 'start' in ks_syncing_field and 'end' in ks_syncing_field:
            # Finding duplicates in office
            _subject_start_end = list()
            for ks_event in ks_all_office_events:
                _start = datetime.strptime(ks_event['start']['dateTime'].split('.')[0].replace('T', ' '),
                                           '%Y-%m-%d %H:%M:%S')
                _end = datetime.strptime(ks_event['end']['dateTime'].split('.')[0].replace('T', ' '),
                                         '%Y-%m-%d %H:%M:%S')
                if _subject_start_end.count((ks_event['subject'], ks_event['start']['dateTime'],
                                             ks_event['end']['dateTime'])) == 1:
                    self.ks_create_log("calendar", ks_event['subject'], ks_event['id'], 0,
                                       ks_current_datatime, "office_to_odoo", False, "failed",
                                       _("Multiple event with the same subject \'" + ks_event['subject'] +
                                         "\', start datetime \'" + str(_start) + "\' and end datetime \'" +
                                         str(_end) + "\' exists in in Office 365.\nNote: This event is being "
                                                     "synced with respect to subject, start datetime end datetime."))
                    ks_office_duplicate_subject_start_end.add((ks_event['subject'], _start, _end))
                _subject_start_end.append((ks_event['subject'], ks_event['start']['dateTime'],
                                           ks_event['end']['dateTime']))

        sync_error = False
        for ks_e in ks_office_events:
            ks_events_imported += 1

            """ Syncing deleted tasks """
            if self.ks_sync_deleted_event:
                is_deleted = self.ks_sync_event_deleted_in_odoo(ks_e, ks_head)
                if is_deleted:
                    continue

            ks_location = self.ks_get_event_locations(ks_e)
            ks_start = self.ks_get_event_start_date(ks_e)
            ks_end = self.ks_get_event_stop_date(ks_e)
            ks_alarm_ids = self.ks_get_alarm_id(ks_e)
            ks_attendees = self.ks_get_office365_attendees(ks_e)

            ks_start_datetime = False
            ks_stop_datetime = False
            ks_start_date = False
            ks_stop_date = False
            if not ks_e['isAllDay']:
                ks_start_datetime = ks_start
                ks_stop_datetime = ks_end
            else:
                ks_start_date = ks_start.date()
                ks_stop_date = ks_end.date()
                ks_start = ks_start.replace(hour=8)
                ks_end = ks_end.replace(hour=18, minute=0, second=0)

            ks_recurrency = True if ks_e['recurrence'] else False
            ks_vals = {
                "description": ks_e['bodyPreview'],
                "name": ks_e['subject'],
                "location": ks_location,
                "start": str(ks_start),
                "stop": str(ks_end),
                "ks_user_id": self.id,
                "ks_office_event_id": ks_e['id'],
                "allday": ks_e['isAllDay'],
                "show_as": ks_e['showAs'] if ks_e['showAs'] in ['free', 'busy'] else False,
                "start_datetime": str(ks_start_datetime) if ks_start_datetime else ks_start_datetime,
                "stop_datetime": str(ks_stop_datetime) if ks_stop_datetime else ks_stop_datetime,
                "start_date": ks_start_date,
                "stop_date": ks_stop_date,
                "alarm_ids": [(6, 0, ks_alarm_ids.ids)] if ks_alarm_ids else None,
                "partner_ids": [(6, 0, ks_attendees.ids)] if ks_attendees else None,
                "privacy": 'public' if ks_e['sensitivity'] == 'normal' else 'private',
                "recurrency": ks_recurrency,
                "ks_rec_type_noend": False,
            }

            ks_range = None
            ks_month_by = None
            ks_pattern = None
            ks_rule_type = None
            _mo = False
            _tu = False
            _we = False
            _th = False
            _fr = False
            _sa = False
            _su = False
            if ks_recurrency:
                ks_range = ks_e['recurrence']['range']
                ks_pattern = ks_e['recurrence']['pattern']
                ks_rule_type = self.ks_get_rule_type(ks_pattern)

                if "daysOfWeek" in ks_pattern:
                    if ks_pattern['type'] == "weekly":
                        if "monday" in ks_pattern["daysOfWeek"]:
                            _mo = True
                        if "tuesday" in ks_pattern["daysOfWeek"]:
                            _tu = True
                        if "wednesday" in ks_pattern["daysOfWeek"]:
                            _we = True
                        if "thursday" in ks_pattern["daysOfWeek"]:
                            _th = True
                        if "friday" in ks_pattern["daysOfWeek"]:
                            _fr = True
                        if "saturday" in ks_pattern["daysOfWeek"]:
                            _sa = True
                        if "sunday" in ks_pattern["daysOfWeek"]:
                            _su = True

                if ks_pattern['type'] in ["relativeMonthly", "relativeYearly"]:
                    ks_month_by = "day"
                elif ks_pattern['type'] == ["absoluteMonthly", "absoluteYearly"]:
                    ks_month_by = "date"
                else:
                    ks_month_by = ""

                ks_week_list = {'monday': 'MO', 'tuesday': 'TU', 'wednesday': 'WE', 'thursday': 'TH', 'friday': 'FR',
                                'saturday': 'SA', 'sunday': 'SU'}

                ks_final_date = self.ks_get_final_date(ks_e['recurrence'])
                ks_vals = {
                    "description": ks_e['bodyPreview'],
                    "name": ks_e['subject'],
                    "location": ks_location,
                    "start": str(ks_start),
                    "stop": str(ks_end),
                    "ks_user_id": self.id,
                    "ks_office_event_id": ks_e['id'],
                    "allday": ks_e['isAllDay'],
                    "show_as": ks_e['showAs'] if ks_e['showAs'] in ['free', 'busy'] else False,
                    "alarm_ids": [(6, 0, ks_alarm_ids.ids)] if ks_alarm_ids else None,
                    "partner_ids": [(6, 0, ks_attendees.ids)] if ks_attendees else None,
                    "privacy": 'public' if ks_e['sensitivity'] == 'normal' else 'private',

                    "recurrency": True,
                    "interval": ks_pattern['interval'],
                    "rrule_type": ks_rule_type,
                    "month_by": ks_month_by,
                    "count": 1,
                    "day": ks_start.day,
                    "week_list": ks_week_list[ks_pattern['daysOfWeek'][0]] if 'daysOfWeek' in ks_pattern else False,
                    "byday": "1",
                    "mo": _mo,
                    "tu": _tu,
                    "we": _we,
                    "th": _th,
                    "fr": _fr,
                    "sa": _sa,
                    "su": _su,
                    "end_type": "end_date" if ks_range['type'] in ['endDate', 'noEnd'] else "count",
                    "final_date": ks_final_date,
                    "ks_rec_type_noend": True if ks_range['type'] == 'noEnd' else False,
                }

            if ks_e['id'] in ks_existing_odoo_events.mapped('ks_office_event_id'):
                if 'subject' in ks_syncing_field and 'start' not in ks_syncing_field and 'end' not in ks_syncing_field:
                    if ks_e['subject'] in ks_office_duplicate_subject:
                        continue

                elif 'subject' in ks_syncing_field and 'start' in ks_syncing_field and 'end' not in ks_syncing_field:
                    _start = datetime.strptime(ks_e['start']['dateTime'].split('.')[0].replace('T', ' '),
                                               '%Y-%m-%d %H:%M:%S')
                    if (ks_e['subject'], _start) in ks_office_duplicate_subject_start:
                        continue

                elif 'subject' in ks_syncing_field and 'end' in ks_syncing_field and 'start' not in ks_syncing_field:
                    _end = datetime.strptime(ks_e['end']['dateTime'].split('.')[0].replace('T', ' '),
                                             '%Y-%m-%d %H:%M:%S')
                    if (ks_e['subject'], str(_end)) in ks_office_duplicate_subject_end:
                        continue

                elif 'subject' in ks_syncing_field and 'start' in ks_syncing_field and 'end' in ks_syncing_field:
                    _start = datetime.strptime(ks_e['start']['dateTime'].split('.')[0].replace('T', ' '),
                                               '%Y-%m-%d %H:%M:%S')
                    _end = datetime.strptime(ks_e['end']['dateTime'].split('.')[0].replace('T', ' '),
                                             '%Y-%m-%d %H:%M:%S')
                    if (ks_e['subject'], _start, _end) in ks_office_duplicate_subject_start_end:
                        continue

                _ev_id = list(set(
                    get_real_ids(self.env['calendar.event'].search([('ks_office_event_id', '=', ks_e['id'])]).ids)))
                ks_event = self.env['calendar.event'].browse(_ev_id)
                temp = self.sudo().env['ks_office365.settings'].search([], limit=1)
                temp.ks_dont_sync = True
                ks_some_error = self.ks_update_events(ks_event, ks_e, ks_recurrency, ks_location,
                                                      ks_alarm_ids, ks_attendees, ks_pattern, ks_rule_type,
                                                      ks_month_by, ks_start, ks_end, ks_range, _mo, _tu, _we, _th,
                                                      _fr, _sa, _su, ks_vals)
                temp.ks_dont_sync = False
                ks_current_job.write({'ks_records': ks_events_imported})
                if ks_some_error:
                    sync_error = True

            elif 'subject' in ks_syncing_field and 'start' not in ks_syncing_field and 'end' not in ks_syncing_field:
                if ks_e['subject'] in ks_office_duplicate_subject:
                    continue
                ks_event = []
                if ks_e['recurrence']:
                    _final = ks_e['recurrence']['range']['endDate']
                    _ev_ids = list(
                        set(get_real_ids(self.env['calendar.event'].search([('name', '=', ks_e['subject'])]).ids)))
                    for _id in _ev_ids:
                        _ev = self.env['calendar.event'].browse(_id)
                        if _ev.name == ks_e['subject']:
                            ks_event.append(_ev)
                else:
                    ks_event = self.env['calendar.event'].search([('name', '=', ks_e['subject'])])

                if len(ks_event) > 1:
                    self.ks_create_log("calendar", ks_e['subject'], '', ks_event.mapped('id'),
                                       ks_current_datatime,
                                       "office_to_odoo", "update", "failed",
                                       _("Multiple event with the same subject \'" + ks_e['subject'] +
                                         "\' exists in Odoo.\nNote: This event is being synced with respect to "
                                         "subject."))
                    continue
                elif len(ks_event) == 1:
                    ks_some_error = self.ks_update_events(ks_event[0], ks_e, ks_recurrency, ks_location, ks_alarm_ids,
                                                          ks_attendees, ks_pattern, ks_rule_type, ks_month_by,
                                                          ks_start, ks_end, ks_range, _mo, _tu, _we, _th, _fr, _sa,
                                                          _su, ks_vals)
                    ks_current_job.write({'ks_records': ks_events_imported})
                    if ks_some_error:
                        sync_error = True
                else:
                    event = self.env['calendar.event'].create(ks_vals)
                    self.ks_create_log("calendar", event.name, event.ks_office_event_id, event.id.__str__(),
                                       ks_current_datatime, "office_to_odoo", "create", "success",
                                       _("Record created!"))

            elif 'subject' in ks_syncing_field and 'start' in ks_syncing_field and 'end' not in ks_syncing_field:
                _start = datetime.strptime(ks_e['start']['dateTime'].split('.')[0].replace('T', ' '),
                                           '%Y-%m-%d %H:%M:%S')
                if (ks_e['subject'], _start) in ks_office_duplicate_subject_start:
                    continue

                if ks_e['isAllDay']:
                    _start = _start.replace(hour=8)

                ks_event = []
                if ks_e['recurrence']:
                    _final = ks_e['recurrence']['range']['endDate']
                    _ev_ids = list(set(get_real_ids(self.env['calendar.event']
                                                    .search([('name', '=', ks_e['subject']),
                                                             ('start', '=', str(_start))]).ids)))
                    _start = ks_e['recurrence']['range']['startDate']
                    for _id in _ev_ids:
                        _ev = self.env['calendar.event'].browse(_id)
                        if _ev.name == ks_e['subject'] and str(_ev.start.date()) == _start:
                            ks_event.append(_ev)
                else:
                    ks_event = self.env['calendar.event'].search([('name', '=', ks_e['subject']),
                                                                  ('start', '=', str(_start))])
                if len(ks_event) > 1:
                    self.ks_create_log("calendar", ks_e['subject'], '', ks_event.mapped('id'),
                                       ks_current_datatime,
                                       "office_to_odoo", "update", "failed",
                                       _("Multiple event with the same subject \'" + ks_e['subject'] +
                                         "\' and start datetime \'" + str(_start) +
                                         "\' exists in Odoo.\nNote: This event is being synced with respect to "
                                         "subject and start datetime."))
                    continue
                elif len(ks_event) == 1:
                    ks_some_error = self.ks_update_events(ks_event[0], ks_e, ks_recurrency, ks_location, ks_alarm_ids,
                                                          ks_attendees, ks_pattern, ks_rule_type, ks_month_by,
                                                          ks_start, ks_end, ks_range, _mo, _tu, _we, _th, _fr, _sa, _su,
                                                          ks_vals)
                    ks_current_job.write({'ks_records': ks_events_imported})
                    if ks_some_error:
                        sync_error = True
                else:
                    event = self.env['calendar.event'].create(ks_vals)
                    self.ks_create_log("calendar", event.name, event.ks_office_event_id, event.id.__str__(),
                                       ks_current_datatime, "office_to_odoo", "create", "success",
                                       _("Record created!"))

            elif 'subject' in ks_syncing_field and 'end' in ks_syncing_field and 'start' not in ks_syncing_field:
                _end = datetime.strptime(ks_e['end']['dateTime'].split('.')[0].replace('T', ' '), '%Y-%m-%d %H:%M:%S')
                if (ks_e['subject'], str(_end)) in ks_office_duplicate_subject_end:
                    continue
                if ks_e['isAllDay']:
                    _end = _end + relativedelta(seconds=-1)
                    _end = _end.replace(hour=18, minute=0, second=0)

                ks_event = []
                if ks_e['recurrence']:
                    _final = ks_e['recurrence']['range']['endDate']
                    _ev_ids = list(set(get_real_ids(self.env['calendar.event'].search([('name', '=', ks_e['subject']),
                                                                                       ('stop', '=', str(_end))]).ids)))
                    _start = ks_e['recurrence']['range']['startDate']
                    for _id in _ev_ids:
                        _ev = self.env['calendar.event'].browse(_id)
                        if _ev.name == ks_e['subject'] and str(_ev.final_date) == _final:
                            ks_event.append(_ev)
                else:
                    ks_event = self.env['calendar.event'].search([('name', '=', ks_e['subject']),
                                                                  ('stop', '=', str(_end))])
                if len(ks_event) > 1:
                    self.ks_create_log("calendar", ks_e['subject'], '', ks_event.mapped('id'),
                                       ks_current_datatime,
                                       "office_to_odoo", "update", "failed",
                                       _("Multiple event with the same subject \'" + ks_e['subject'] +
                                         "\' and end datetime \'" + str(_end) +
                                         "\' exists in Odoo.\nNote: This event is being synced with respect to "
                                         "subject and end datetime."))
                    continue
                elif len(ks_event) == 1:
                    ks_some_error = self.ks_update_events(ks_event[0], ks_e, ks_recurrency, ks_location, ks_alarm_ids,
                                                          ks_attendees, ks_pattern, ks_rule_type, ks_month_by,
                                                          ks_start, ks_end, ks_range, _mo, _tu, _we, _th, _fr, _sa, _su,
                                                          ks_vals)
                    ks_current_job.write({'ks_records': ks_events_imported})
                    if ks_some_error:
                        sync_error = True
                else:
                    event = self.env['calendar.event'].create(ks_vals)
                    self.ks_create_log("calendar", event.name, event.ks_office_event_id, event.id.__str__(),
                                       ks_current_datatime, "office_to_odoo", "create", "success",
                                       _("Record created!"))

            elif 'subject' in ks_syncing_field and 'start' in ks_syncing_field and 'end' in ks_syncing_field:
                _start = datetime.strptime(ks_e['start']['dateTime'].split('.')[0].replace('T', ' '),
                                           '%Y-%m-%d %H:%M:%S')
                _end = datetime.strptime(ks_e['end']['dateTime'].split('.')[0].replace('T', ' '), '%Y-%m-%d %H:%M:%S')
                if (ks_e['subject'], _start, _end) in ks_office_duplicate_subject_start_end:
                    continue
                if ks_e['isAllDay']:
                    _end = _end + relativedelta(seconds=-1)
                    _start = _start.replace(hour=8)
                    _end = _end.replace(hour=18, minute=0, second=0)

                ks_event = []
                if ks_e['recurrence']:
                    _final = ks_e['recurrence']['range']['endDate']
                    _ev_ids = list(set(get_real_ids(self.env['calendar.event'].search([('name', '=', ks_e['subject']),
                                                                                       ('start', '=', str(_start)),
                                                                                       ('stop', '=', str(_end))]).ids)))
                    _start = ks_e['recurrence']['range']['startDate']
                    for _id in _ev_ids:
                        _ev = self.env['calendar.event'].browse(_id)
                        if _ev.name == ks_e['subject'] and _ev.start.split(' ')[0] == _start and \
                                str(_ev.final_date) == _final:
                            ks_event.append(_ev)
                else:
                    ks_event = self.env['calendar.event'].search([('name', '=', ks_e['subject']),
                                                                  ('start', '=', str(_start)),
                                                                  ('stop', '=', str(_end))])

                if len(ks_event) > 1:
                    error_message = _("Multiple event with the same subject \'" + ks_e['subject'] +
                                      "\', start datetime \'" + ks_e['start']['dateTime'] + "\' and end datetime \'" +
                                      ks_e['end']['dateTime'] +
                                      "\' exists in Odoo.\nNote: This event is being synced with respect to subject, "
                                      "start datetime and end datetime.")
                    self.ks_create_log("calendar", ks_e['subject'], '', ks_event.mapped('id'),
                                       ks_current_datatime, "office_to_odoo", "update", "failed", error_message)
                    continue
                elif len(ks_event) == 1:
                    ks_some_error = self.ks_update_events(ks_event[0], ks_e, ks_recurrency, ks_location, ks_alarm_ids,
                                                          ks_attendees, ks_pattern, ks_rule_type, ks_month_by,
                                                          ks_start, ks_end, ks_range, _mo, _tu, _we, _th, _fr, _sa, _su,
                                                          ks_vals)
                    ks_current_job.write({'ks_records': ks_events_imported})
                    if ks_some_error:
                        sync_error = True
                else:
                    temp = self.sudo().env['ks_office365.settings'].search([], limit=1)
                    temp.ks_dont_sync = True
                    event = self.env['calendar.event'].create(ks_vals)
                    temp.ks_dont_sync = False
                    self.ks_create_log("calendar", event.name, event.ks_office_event_id, event.id.__str__(),
                                       ks_current_datatime, "office_to_odoo", "create", "success",
                                       _("Record created!"))

        if not sync_error:
            ks_current_job.write({'ks_status': 'completed'})
            return self.sudo().ks_no_sync_error()
        else:
            ks_current_job.write({'ks_status': 'completed'})
            return self.ks_has_sync_error()

    def ks_sync_event_deleted_in_odoo(self, ks_office_event, header):
        ks_del_event = self.env['ks.deleted'].search([('ks_office_id', '=', ks_office_event['id']),
                                                      ('ks_user_id', '=', self.id)])
        if ks_del_event:
            url = "https://graph.microsoft.com/v1.0/me/events/%s" % ks_office_event['id']
            response = requests.delete(url, headers=header)
            result = json.loads(response.text)
            if response.status_code == 204:
                self.ks_create_log("calendar", ks_office_event['subject'], ks_office_event['id'], 0,
                                   datetime.today(), "office_to_odoo", "delete", "success",
                                   _("Event deleted from outlook Calendar"))
                return True
            else:
                self.ks_create_log("calendar", ks_office_event['subject'], ks_office_event['id'], 0,
                                   datetime.today(), "office_to_odoo", "delete", "failed",
                                   _("Event not deleted from outlook Calendar"))
        return False

    def ks_get_final_date(self, ks_recurrence):
        final_date = ks_recurrence['range']['endDate']
        if ks_recurrence['range']['type'] == 'noEnd':
            today = datetime.today().date()
            start = datetime.strptime(ks_recurrence['range']['startDate'], '%Y-%m-%d').date()
            if start > today:
                today = start
            if ks_recurrence['pattern']['type'] in ['daily', 'weekly']:
                final_date = today + relativedelta(months=1)
            elif ks_recurrence['pattern']['type'] in ["relativeMonthly", "absoluteMonthly"]:
                final_date = today + relativedelta(months=5)
            elif ks_recurrence['pattern']['type'] in ["relativeYearly", "absoluteYearly"]:
                final_date = today + relativedelta(years=5)
        return str(final_date)

    def ks_update_events(self, event, ks_e, ks_recurrency, ks_location, ks_alarm_ids, ks_attendees, ks_pattern,
                         ks_rule_type, ks_month_by, ks_start, ks_end, ks_range, _mo, _tu, _we, _th, _fr, _sa, _su,
                         ks_vals):
        ks_some_error = False
        try:
            if event[0].recurrency and ks_recurrency:
                ks_week_list = {'monday': 'MO', 'tuesday': 'TU', 'wednesday': 'WE', 'thursday': 'TH', 'friday': 'FR',
                                'saturday': 'SA', 'sunday': 'SU'}
                ks_final_date = self.ks_get_final_date(ks_e['recurrence'])
                ks_recurr_vals = {
                    "description": ks_e['bodyPreview'],
                    "name": ks_e['subject'],
                    "location": ks_location,
                    "ks_user_id": self.id,
                    "ks_office_event_id": ks_e['id'],
                    "allday": ks_e['isAllDay'],
                    "show_as": ks_e['showAs'] if ks_e['showAs'] in ['free', 'busy'] else False,
                    "alarm_ids": [(6, 0, ks_alarm_ids.ids)] if ks_alarm_ids else None,
                    "partner_ids": [(6, 0, ks_attendees.ids)] if ks_attendees else None,
                    "privacy": 'public' if ks_e['sensitivity'] == 'normal' else 'private',

                    "recurrency": True,
                    "interval": ks_pattern['interval'],
                    "rrule_type": ks_rule_type,
                    "month_by": ks_month_by,
                    "count": 1,
                    "day": ks_start.day,
                    "week_list": ks_week_list[ks_pattern['daysOfWeek'][0]] if 'daysOfWeek' in ks_pattern else False,
                    "byday": "1",
                    "mo": _mo,
                    "tu": _tu,
                    "we": _we,
                    "th": _th,
                    "fr": _fr,
                    "sa": _sa,
                    "su": _su,
                    "end_type": "end_date" if ks_range['type'] in ['endDate', 'noEnd'] else "count",
                    "final_date": ks_final_date,
                    "ks_rec_type_noend": True if ks_range['type'] == 'noEnd' else False,
                }
                ks_real_id = event[0].id
                real_event = self.env['calendar.event'].browse(ks_real_id)
                # Not able to set privacy of an event with cron as user will be admin and rights to update for
                # other users is not given to him
                real_event.sudo().write(ks_recurr_vals)
                real_event.sudo().write({'rrule': real_event._rrule_serialize()})
                real_event.sudo().write({'day': ks_start.day})

                self.ks_create_log("calendar", real_event.name, real_event.ks_office_event_id,
                                   str(real_event.id), datetime.today(), "office_to_odoo", "update",
                                   "success", _("Record updated!"))
            elif event[0].recurrency:
                ks_real_id = event[0].id
                real_event = self.env['calendar.event'].browse(ks_real_id)
                real_event.sudo().write(ks_vals)
                self.ks_create_log("calendar", real_event.name, real_event.ks_office_event_id,
                                   str(real_event.id), datetime.today(), "office_to_odoo", "update",
                                   "success", _("Record updated!"))
            elif not event[0].recurrency and ks_recurrency:
                ks_vals.update({'rrule': event[0]._rrule_serialize()})
                event.sudo().write(ks_vals)
                self.ks_create_log("calendar", event.name, event.ks_office_event_id, event.id.__str__(),
                                   datetime.today(), "office_to_odoo", "update", "success",
                                   _("Record updated!"))
            else:
                event.sudo().write(ks_vals)
                self.ks_create_log("calendar", event.name, event.ks_office_event_id, event.id.__str__(),
                                   datetime.today(), "office_to_odoo", "update", "success",
                                   _("Record updated!"))

        except Exception as ex:
            self.ks_create_log("calendar", event.name, ks_e['id'], event.id,
                               datetime.today(), "office_to_odoo", "update", "failed", _(ex))
            ks_some_error = True

        return ks_some_error

    def ks_get_calendar_search_domain(self, ks_sync_event_from_date):
        ks_search_domain = [('ks_user_id', '=', self.id)]
        if self.ks_calendar_filter_domain:
            for d in eval(self.ks_calendar_filter_domain):
                if type(d) is list:
                    ks_search_domain.append(tuple(d))

        ks_search_domain.append(('write_date', '>=', str(ks_sync_event_from_date)))
        return ks_search_domain

    def ks_post_events(self, q_context, ks_individual_event=None):
        try:
            if not ks_individual_event:
                if self.ks_calendar_sync_using_days:
                    _days = str(self.ks_calendar_sync_days_before)
                    if not (_days.isdigit() and not len(_days) > 3) or int(_days) < 0:
                        return self.ks_show_error_message(
                            _("Days can only be in numbers less then 999 and greater than or equal to 0."))
            res = self.ks_export_events(ks_individual_event)
            return res
        except Exception as ex:
            if type(ex) is requests.exceptions.ConnectionError:
                ex = "Internet Connection Failed"
            ks_current_job = self.env["ks.office.job"].search(
                [('ks_records', '>=', 0), ('ks_status', '=', 'in_process'),
                 ('ks_job', '=', 'calendar_export'),
                 ('create_uid', '=', self.env.user.id)])
            if ks_current_job:
                ks_current_job.write({'ks_status': 'error', 'ks_error_text': ex})
                self.env.cr.commit()
            self.ks_create_log("calendar", "Error", "", 0, datetime.today(), "odoo_to_office", False, "failed",
                               _(str(ex) + "\nCheck Jobs to know how many records have been processed."))
            return self.ks_has_sync_error()

    def ks_get_odoo_events(self, sync_from, all_events=False):
        query = "select * from calendar_event where id in " \
                "(select calendar_event_id from calendar_event_res_partner_rel where res_partner_id = %(id)s)"
        self._cr.execute(query, {'id': self.partner_id.id})
        ks_search_domain = [('id', 'in', [event['id'] for event in self.env.cr.dictfetchall()]),
                            ('create_uid', '=', self.id)]
        if not all_events:
            if self.ks_calendar_filter_domain:
                for d in eval(self.ks_calendar_filter_domain):
                    if type(d) is list:
                        ks_search_domain.append(tuple(d))

            ks_search_domain.append(('write_date', '>=', str(sync_from)))

        return self.env['calendar.event'].search(ks_search_domain)

    def ks_export_events(self, ks_individual_event):
        ks_current_datatime = datetime.today()
        ks_api_endpoint = "https://graph.microsoft.com/v1.0/me/events?$top=1000000"
        ks_auth_token = self.ks_auth_token

        if not ks_auth_token:
            self.ks_create_log("authentication", "Authentication", "", 0, ks_current_datatime,
                               "odoo_to_office", "authentication", "failed", _("Generate Authentication Token"))
            return self.ks_show_error_message(_('Generate Authentication Token'))

        ks_head = {
            "Authorization": ks_auth_token,
            "Content-Type": "application/json"
        }
        ks_current_job = None

        # for finding duplicate events in odoo
        ks_duplicate_odoo_subject = set()
        ks_duplicate_odoo_subject_start = set()
        ks_duplicate_odoo_subject_end = set()
        ks_duplicate_odoo_subject_start_end = set()
        if not ks_individual_event:
            ks_current_job = self.ks_is_job_completed("calendar_export", "calendar")
            if not ks_current_job:
                return self.ks_show_error_message(_('Process Is Already Running.'))
            else:
                ks_current_job.write({'ks_status': 'in_process'})

            ks_sync_event_from_date = datetime.min.date().replace(year=1900)
            if self.ks_calendar_sync_using_days:
                ks_days = self.ks_calendar_sync_days_before
                ks_sync_event_from_date = ks_current_datatime.date() + relativedelta(days=-ks_days)

            ks_odoo_events = self.env['calendar.event'].browse(
                list(set(get_real_ids(self.ks_get_odoo_events(ks_sync_event_from_date).ids)))
            )

            # For finding duplicates
            ks_all_odoo_events = self.env['calendar.event'].browse(
                list(set(get_real_ids(self.ks_get_odoo_events(ks_sync_event_from_date, all_events=True).ids)))
            )

            ks_office_response = requests.get(ks_api_endpoint, headers=ks_head)
            ks_office_events_json_data = json.loads(ks_office_response.text)

            if 'error' in ks_office_events_json_data:
                if ks_office_events_json_data["error"]['code'] == 'InvalidAuthenticationToken':
                    self.refresh_token()
                    ks_head['Authorization'] = self.ks_auth_token
                    ks_office_response = requests.get(ks_api_endpoint, headers=ks_head)
                    ks_office_events_json_data = json.loads(ks_office_response.text)
                    if 'error' in ks_office_events_json_data:
                        self.ks_create_log("authentication", "Authentication", "", 0, ks_current_datatime,
                                           "odoo_to_office", "authentication", "failed",
                                           _(ks_office_events_json_data["error"]['code']))
                        return self.ks_show_error_message(
                            _("Some error occurred! \nPlease check logs for more information."))
                else:
                    self.ks_create_log("authentication", "Authentication", "", 0, ks_current_datatime,
                                       "odoo_to_office",
                                       "authentication", "failed",
                                       _(ks_office_events_json_data["error"]['code']))
                    return self.ks_show_error_message(
                        _("Some error occurred! \nPlease check logs for more information."))

            ks_office_events = ks_office_events_json_data['value']

            ks_syncing_field = list()
            if self.ks_calendar_sync_using_subject:
                ks_syncing_field.append("subject")
            if self.ks_calendar_sync_using_start_datetime:
                ks_syncing_field.append("start")
            if self.ks_calendar_sync_using_end_datetime:
                ks_syncing_field.append("end")

            # Finding duplicate events in Odoo
            if 'subject' in ks_syncing_field and 'start' not in ks_syncing_field and 'end' not in ks_syncing_field:
                _subject = list()
                for ks_event in ks_all_odoo_events:
                    if _subject.count(ks_event.name) == 1:
                        self.ks_create_log("calendar", ks_event.name, ks_event.ks_office_event_id, ks_event.id,
                                           ks_current_datatime, "odoo_to_office", "update", "failed",
                                           _("Multiple events with same subject \'" + ks_event.name +
                                             "\' exists in Odoo. \nNote: This event is being synced with respect to subject."))
                        ks_duplicate_odoo_subject.add(ks_event.name)
                    _subject.append(ks_event.name)

            elif 'subject' in ks_syncing_field and 'start' in ks_syncing_field and 'end' not in ks_syncing_field:
                _subject_start = list()
                for ks_event in ks_all_odoo_events:
                    if _subject_start.count((ks_event.name, ks_event.start)) == 1:
                        self.ks_create_log("calendar", ks_event.name, ks_event.ks_office_event_id, ks_event.id,
                                           ks_current_datatime, "odoo_to_office", "update", "failed",
                                           _(
                                               "Multiple events with same subject \'" + ks_event.name + "\' and start datetime \'"
                                               + str(
                                                   ks_event.start) + "\' exists in Odoo. \nNote: This event is being synced "
                                                                     "with respect to subject and start datetime."))
                        ks_duplicate_odoo_subject_start.add((ks_event.name, ks_event.start))
                    _subject_start.append((ks_event.name, ks_event.start))

            elif 'subject' in ks_syncing_field and 'end' in ks_syncing_field and 'start' not in ks_syncing_field:
                _subject_end = list()
                for ks_event in ks_all_odoo_events:
                    if _subject_end.count((ks_event.name, ks_event.stop)) == 1:
                        self.ks_create_log("calendar", ks_event.name, ks_event.ks_office_event_id, ks_event.id,
                                           ks_current_datatime, "odoo_to_office", "update", "failed",
                                           _(
                                               "Multiple events with same subject \'" + ks_event.name + "\' and end datetime \'"
                                               + str(
                                                   ks_event.stop) + "\' exists in Odoo. \nNote: This event is being synced "
                                                                    "with respect to subject and end datetime."))
                        ks_duplicate_odoo_subject_end.add((ks_event.name, ks_event.stop))
                    _subject_end.append((ks_event.name, ks_event.stop))

            elif 'subject' in ks_syncing_field and 'start' in ks_syncing_field and 'end' in ks_syncing_field:
                _subject_start_end = list()
                for ks_event in ks_all_odoo_events:
                    if _subject_start_end.count((ks_event.name, ks_event.start, ks_event.stop)) == 1:
                        error_message = _("Multiple events with same subject \'" + ks_event.name +
                                          "\', start datetime \'" + str(ks_event.start) + "\' and end datetime \'" +
                                          str(ks_event.stop) +
                                          "\' exists in Odoo. \nNote: This event is being synced with respect to "
                                          "subject, start datetime and end datetime.")
                        self.ks_create_log("calendar", ks_event.name, ks_event.ks_office_event_id, ks_event.id,
                                           ks_current_datatime, "odoo_to_office", "update", "failed",
                                           error_message)
                        ks_duplicate_odoo_subject_start_end.add((ks_event.name, ks_event.start, ks_event.stop))
                    _subject_start_end.append((ks_event.name, ks_event.start, ks_event.stop))

            ks_events_exported = ks_current_job.ks_records

        else:
            ks_odoo_events = ks_individual_event
            ks_events_exported = 0

        sync_error = False
        ks_recurrent_already_done = []
        for event in ks_odoo_events[ks_events_exported:]:

            """ Sync deleted events in Outlook """
            if self.ks_sync_deleted_office_event(event, ks_head):
                continue

            if not event.ks_is_updated:
                continue
            ks_events_exported += 1
            if event.recurrency:
                ks_real_id = get_real_ids(event.id)
                if ks_real_id in ks_recurrent_already_done:
                    continue
                else:
                    event = self.env['calendar.event'].browse(ks_real_id)
                    ks_recurrent_already_done.append(ks_real_id)
            ks_attendees = []
            for attend in event.attendee_ids:
                if self.partner_id == attend.partner_id:
                    continue
                _temp = {
                    "emailAddress": {
                        "address": attend.email or "",
                        "name": attend.display_name
                    },
                    "type": "required"
                }
                ks_attendees.append(_temp)

            event_start = datetime.strptime(event.start, '%Y-%m-%d %H:%M:%S')
            event_stop = datetime.strptime(event.stop, '%Y-%m-%d %H:%M:%S')
            if event.allday:
                _start = event_start.replace(hour=8)
                _stop = event_stop.replace(hour=18, minute=0, second=0)
                start_date = self.ks_datetime_from_utc_to_local(_start).split('T')[0] + "T00:00:00.0000000"
                if event.allday and event_stop.date() != event_start.date():
                    stop = _stop + timedelta(days=1)
                    stop_date = self.ks_datetime_from_utc_to_local(stop).split('T')[0] + "T00:00:00.0000000"
                else:
                    stop = _stop + timedelta(days=1)
                    stop_date = self.ks_datetime_from_utc_to_local(stop).split('T')[0] + "T00:00:00.0000000"
            else:
                start_date = self.ks_datetime_from_utc_to_local(event_start)
                stop_date = self.ks_datetime_from_utc_to_local(event_stop + relativedelta(seconds=10))

            locations = self.ks_get_odoo_locations(event)

            ks_recurrence = None
            if event.recurrency:
                ks_recurrence = self.ks_get_event_recurrency(event)

            data = {
                "subject": event.display_name,
                "body": {
                    "contentType": "HTML",
                    "content": "" if not event.description else event.description
                },
                "start": {
                    "dateTime": start_date.__str__(),
                    "timeZone": fields.Datetime.context_timestamp(self, datetime.now()).tzinfo.zone
                },
                "end": {
                    "dateTime": stop_date.__str__(),
                    "timeZone": fields.Datetime.context_timestamp(self, datetime.now()).tzinfo.zone
                },
                "locations": locations if locations else [],
                "attendees": ks_attendees,
                "isAllDay": event.allday,
                "recurrence": ks_recurrence,
                "showAs": event.show_as,
                "isReminderOn": False if not event.alarm_ids else True,
                "reminderMinutesBeforeStart": 15 if not event.alarm_ids else event.alarm_ids[0].duration_minutes,
                "sensitivity": "Normal" if event.privacy == "public" else "private"
            }

            if not event.show_as:
                data.pop('showAs')

            if event.ks_office_event_id != "":
                if not ks_individual_event:
                    if 'subject' in ks_syncing_field and 'start' not in ks_syncing_field and 'end' not in ks_syncing_field:
                        if event.name in ks_duplicate_odoo_subject:
                            continue
                    elif 'subject' in ks_syncing_field and 'start' in ks_syncing_field and 'end' not in ks_syncing_field:
                        if (event.name, event.start) in ks_duplicate_odoo_subject_start:
                            continue
                    elif 'subject' in ks_syncing_field and 'end' in ks_syncing_field and 'start' not in ks_syncing_field:
                        if (event.name, event.stop) in ks_duplicate_odoo_subject_end:
                            continue
                    elif 'subject' in ks_syncing_field and 'start' in ks_syncing_field and 'end' in ks_syncing_field:
                        if (event.name, event.start, event.stop) in ks_duplicate_odoo_subject_start_end:
                            continue

                ks_some_error = self.ks_update_office_event(event, ks_head, data, event.ks_office_event_id)
                if not ks_individual_event:
                    ks_current_job.write({'ks_records': ks_events_exported})
                if ks_some_error:
                    sync_error = True

            elif ks_individual_event:
                ks_some_error = self.ks_create_office_event(event, ks_head, data)
                if ks_some_error:
                    sync_error = True

            elif 'subject' in ks_syncing_field and 'start' not in ks_syncing_field and 'end' not in ks_syncing_field:
                _office_id = []
                if event.name in ks_duplicate_odoo_subject:
                    continue
                for ks_o_e in ks_office_events:
                    if ks_o_e['subject'] == event.name:
                        _office_id.append(ks_o_e['id'])

                if len(_office_id) > 1:
                    self.ks_create_log("event", event.name, event.ks_office_event_id, event.id,
                                       ks_current_datatime, "odoo_to_office", "update", "failed",
                                       _("Multiple events with same subject \'" + event.name +
                                         "\' exists in Office 365. \nNote: This event is being synced "
                                         "with respect to subject."))
                    continue
                elif len(_office_id):
                    ks_some_error = self.ks_update_office_event(event, ks_head, data, _office_id[0])
                    ks_current_job.write({'ks_records': ks_events_exported})
                    if ks_some_error:
                        sync_error = True
                else:
                    ks_some_error = self.ks_create_office_event(event, ks_head, data)
                    ks_current_job.write({'ks_records': ks_events_exported})
                    if ks_some_error:
                        sync_error = True

            elif 'subject' in ks_syncing_field and 'start' in ks_syncing_field and 'end' not in ks_syncing_field:
                _office_id = []
                if (event.name, event.start) in ks_duplicate_odoo_subject_start:
                    continue
                for ks_o_e in ks_office_events:
                    if event.allday:
                        _start_office = self.ks_str_datetime_to_datetime(ks_o_e['start']['dateTime'], 'start', allday=1)
                        _start_odoo = event_start.date()
                    else:
                        _start_office = self.ks_str_datetime_to_datetime(ks_o_e['start']['dateTime'], 'start', allday=0)
                        _start_odoo = event_start
                    if ks_o_e['subject'] == event.name and str(_start_office) == str(_start_odoo):
                        _office_id.append(ks_o_e['id'])

                if len(_office_id) > 1:
                    self.ks_create_log("event", event.name, event.ks_office_event_id, event.id,
                                       ks_current_datatime, "odoo_to_office", "update", "failed",
                                       _("Multiple events with same subject \'" + event.name +
                                         "\', start datetime \'" + str(event.start) +
                                         "\' exists in Office 365. \nNote: This event is being synced "
                                         "with respect to subject and start datetime."))
                    continue
                elif len(_office_id):
                    ks_some_error = self.ks_update_office_event(event, ks_head, data, _office_id[0])
                    ks_current_job.write({'ks_records': ks_events_exported})
                    if ks_some_error:
                        sync_error = True
                else:
                    ks_some_error = self.ks_create_office_event(event, ks_head, data)
                    ks_current_job.write({'ks_records': ks_events_exported})
                    if ks_some_error:
                        sync_error = True

            elif 'subject' in ks_syncing_field and 'end' in ks_syncing_field and 'start' not in ks_syncing_field:
                _office_id = []
                if (event.name, event.stop) in ks_duplicate_odoo_subject_end:
                    continue
                for ks_o_e in ks_office_events:
                    if event.allday:
                        _end_office = self.ks_str_datetime_to_datetime(ks_o_e['end']['dateTime'], 'end_1', allday=1)
                        _end_odoo = event_stop.date()
                    else:
                        _end_office = self.ks_str_datetime_to_datetime(ks_o_e['end']['dateTime'], 'end', allday=0)
                        _end_odoo = event_stop

                    if event.recurrency:
                        _end_office = datetime.strptime(ks_o_e['recurrence']['range']['endDate'], '%Y-%m-%d').date()
                        _end_odoo = event.final_date

                    if ks_o_e['subject'] == event.name and str(_end_office) == str(_end_odoo):
                        _office_id.append(ks_o_e['id'])

                if len(_office_id) > 1:
                    self.ks_create_log("event", event.name, event.ks_office_event_id, event.id,
                                       ks_current_datatime, "odoo_to_office", "update", "failed",
                                       _("Multiple events with same subject \'" + event.name +
                                         "\' and end datetime \'" + str(event.stop) +
                                         "\' exists in Office 365. \nNote: This event is being synced with "
                                         "respect to subject and end datetime."))
                    continue
                elif len(_office_id):
                    ks_some_error = self.ks_update_office_event(event, ks_head, data, _office_id[0])
                    ks_current_job.write({'ks_records': ks_events_exported})
                    if ks_some_error:
                        sync_error = True
                else:
                    ks_some_error = self.ks_create_office_event(event, ks_head, data)
                    ks_current_job.write({'ks_records': ks_events_exported})
                    if ks_some_error:
                        sync_error = True

            elif 'subject' in ks_syncing_field and 'start' in ks_syncing_field and 'end' in ks_syncing_field:
                _office_id = []
                if (event.name, event.start, event.stop) in ks_duplicate_odoo_subject_start_end:
                    continue
                for ks_o_e in ks_office_events:
                    if event.allday:
                        _start_office = self.ks_str_datetime_to_datetime(ks_o_e['start']['dateTime'], 'start', allday=1)
                        _end_office = self.ks_str_datetime_to_datetime(ks_o_e['end']['dateTime'], 'end_1', allday=1)
                        _start_odoo = event_start.date()
                        _end_odoo = event_stop.date()
                    else:
                        _start_office = self.ks_str_datetime_to_datetime(ks_o_e['start']['dateTime'], 'start', allday=0)
                        _end_office = self.ks_str_datetime_to_datetime(ks_o_e['end']['dateTime'], 'end', allday=0)
                        _start_odoo = event_start
                        _end_odoo = event_stop

                    if event.recurrency:
                        if ks_o_e['recurrence']:
                            _end_office = datetime.strptime(ks_o_e['recurrence']['range']['endDate'], '%Y-%m-%d').date()
                            _end_odoo = event.final_date

                    if ks_o_e['subject'] == event.name and str(_start_office) == str(_start_odoo) and \
                            str(_end_office) == str(_end_odoo):
                        _office_id.append(ks_o_e['id'])

                if len(_office_id) > 1:
                    self.ks_create_log("event", event.name, event.ks_office_event_id, event.id,
                                       ks_current_datatime, "odoo_to_office", "update", "failed",
                                       _("Multiple events with same subject \'" + event.name + "\', start datetime \'"
                                         + str(event.start) + "\' and end datetime \'" + str(event.stop) +
                                         "\' exists in Office 365. \nNote: This event is being synced "
                                         "with respect to subject, start datetime and end datetime."))
                    continue
                elif len(_office_id):
                    ks_some_error = self.ks_update_office_event(event, ks_head, data, _office_id[0])
                    ks_current_job.write({'ks_records': ks_events_exported})
                    if ks_some_error:
                        sync_error = True
                else:
                    ks_some_error = self.ks_create_office_event(event, ks_head, data)
                    ks_current_job.write({'ks_records': ks_events_exported})
                    if ks_some_error:
                        sync_error = True

        if not sync_error:
            if not ks_individual_event:
                ks_current_job.write({'ks_status': 'completed'})
                return self.ks_no_sync_error()
            return True
        else:
            if not ks_individual_event:
                ks_current_job.write({'ks_status': 'completed'})
                return self.ks_has_sync_error()
            return True

    def ks_sync_deleted_office_event(self, event, ks_head):
        ks_api_endpoint = "https://graph.microsoft.com/v1.0/me/events/" + event.ks_office_event_id
        ks_response = requests.get(ks_api_endpoint, headers=ks_head)
        ks_json_data = json.loads(ks_response.text)
        if 'error' in ks_json_data:
            if ks_response.status_code == 404:
                if self.ks_sync_deleted_event:
                    del_event = {"name": event.name, "office_id": event.ks_office_event_id, "id": event.id}
                    try:
                        event.unlink()
                        self.ks_create_log("calendar", del_event['name'], del_event["office_id"], del_event["id"],
                                           datetime.today(), "odoo_to_office", "delete", "success",
                                           _("Event deleted from Odoo Calendar"))
                    except Exception as ex:
                        self.ks_create_log("calendar", del_event['name'], del_event["office_id"],
                                           del_event["id"], datetime.today(), "odoo_to_office", "delete",
                                           "failed",
                                           _("Record not be deleted from ODOO Calendar \nReason: %s" % ex))
                    return True
        else:
            return False

    def ks_str_datetime_to_datetime(self, dt, type, allday):
        dt = datetime.strptime(dt.split('.')[0].replace('T', ' '), '%Y-%m-%d %H:%M:%S')
        if type == 'end_1':
            dt += relativedelta(seconds=-1)
            # pass
        if allday:
            return dt.date()
        else:
            return dt

    def ks_update_office_event(self, event, ks_head, data, ks_office_id):
        ks_some_error = False
        ks_api_endpoint = "https://graph.microsoft.com/v1.0/me/events/" + ks_office_id
        ks_response = requests.patch(ks_api_endpoint, headers=ks_head, json=data)
        ks_json_data = json.loads(ks_response.text)
        if 'error' in ks_json_data:
            if ks_response.status_code == 404:
                if self.ks_sync_deleted_event:
                    del_event = {"name": event.name, "office_id": event.ks_office_event_id, "id": event.id}
                    try:
                        event.unlink()
                        self.ks_create_log("calendar", del_event['name'], del_event["office_id"], del_event["id"],
                                           datetime.today(), "odoo_to_office", "delete", "success",
                                           _("Event deleted from Odoo Calendar"))
                    except Exception as ex:
                        self.ks_create_log("calendar", del_event['name'], del_event["office_id"],
                                           del_event["id"], datetime.today(), "odoo_to_office", "delete",
                                           "failed",
                                           _("Record not be deleted from ODOO Calendar \nReason: %s" % ex))
                else:
                    ks_some_error = self.ks_create_office_event(event, ks_head, data)
                    if ks_some_error:
                        ks_some_error = True

            elif 'code' in ks_json_data['error']:
                if ks_json_data["error"]['code'] == 'InvalidAuthenticationToken':
                    self.refresh_token()
                    ks_head['Authorization'] = self.ks_auth_token
                    self.ks_update_office_event(event, ks_head, data, ks_office_id)
                else:
                    ks_error = _(ks_json_data['error']['code'] + "\n" + ks_json_data['error']['message'])
                    self.ks_create_log("calendar", event.name, event.ks_office_event_id, event.id.__str__(),
                                       datetime.today(), "odoo_to_office", "update", "failed",
                                       ks_error)
                    ks_some_error = True
            else:
                self.ks_create_log("calendar", event.name, event.ks_office_event_id, event.id.__str__(),
                                   datetime.today(), "odoo_to_office", "update", "failed",
                                   _(ks_json_data['error']['message']))
                ks_some_error = True
        else:
            # Not able to set privacy of an event with cron as user will be admin and rights to update for
            # other users is not given to him
            event.sudo().write({"ks_office_event_id": ks_json_data['id'], 'ks_is_updated': False})
            self.ks_create_log("calendar", event.name, event.ks_office_event_id, event.id.__str__(),
                               datetime.today(), "odoo_to_office", "update", "success", _("Record updated!"))
        return ks_some_error

    def ks_create_office_event(self, event, ks_head, data):
        ks_some_error = False
        ks_api_endpoint = "https://graph.microsoft.com/v1.0/me/events/"
        ks_response = requests.post(ks_api_endpoint, headers=ks_head, json=data)
        ks_json_data = json.loads(ks_response.text)
        if 'error' in ks_json_data:
            if 'code' in ks_json_data['error']:
                if ks_json_data["error"]['code'] == 'InvalidAuthenticationToken':
                    self.refresh_token()
                    ks_head['Authorization'] = self.ks_auth_token
                    self.ks_create_office_event(event, ks_head, data)
                else:
                    ks_error = _(ks_json_data['error']['code'] + "\n" + ks_json_data['error']['message'])
                    self.ks_create_log("calendar", event.name, event.ks_office_event_id, event.id.__str__(),
                                       datetime.today(), "odoo_to_office", "create", "failed",
                                       ks_error)
                    ks_some_error = True
            else:
                ks_error = _(ks_json_data['error']['message'])
                self.ks_create_log("calendar", event.name, event.ks_office_event_id, event.id.__str__(),
                                   datetime.today(), "odoo_to_office", "create", "failed",
                                   ks_error)
                ks_some_error = True
        else:
            # Not able to set privacy of an event with cron as user will be admin and rights to update for
            # other users is not given to him
            event.sudo().write({"ks_office_event_id": ks_json_data['id'], 'ks_is_updated': False})
            self.ks_create_log("calendar", event.name, event.ks_office_event_id, event.id.__str__(),
                               datetime.today(), "odoo_to_office", "create", "success", _("Record created!"))
        return ks_some_error

    def ks_get_rule_type(self, ks_pattern):
        if ks_pattern['type'] == "weekly":
            return "weekly"
        elif ks_pattern['type'] == "absoluteMonthly" or ks_pattern['type'] == "relativeMonthly":
            return "monthly"
        elif ks_pattern['type'] == "daily":
            return "daily"
        else:
            return "yearly"

    def ks_get_event_recurrency(self, event):
        ks_day_of_week = []

        if event.mo:
            ks_day_of_week.append("monday")
        if event.tu:
            ks_day_of_week.append("tuesday")
        if event.we:
            ks_day_of_week.append("wednesday")
        if event.th:
            ks_day_of_week.append("thursday")
        if event.fr:
            ks_day_of_week.append("friday")
        if event.sa:
            ks_day_of_week.append("saturday")
        if event.su:
            ks_day_of_week.append("sunday")

        _rrule_type = ""
        if event.rrule_type == "daily":
            _rrule_type = "daily"
            _pattern = {
                "dayOfMonth": event.day,
                "type": _rrule_type,
                "index": "first",
                "month": 0,
                "interval": event.interval,
                "firstDayofWeek": "sunday",
            }
        elif event.rrule_type == "weekly":
            _rrule_type = "weekly"
            _pattern = {
                "daysOfWeek": ks_day_of_week,
                "dayOfMonth": event.day,
                "type": _rrule_type,
                "index": "first",
                "month": 0,
                "interval": event.interval,
                "firstDayOfWeek": "sunday",
            }
        elif event.rrule_type == "yearly":
            _rrule_type = "absoluteYearly"
            _pattern = {
                "daysOfWeek": ks_day_of_week,
                "dayOfMonth": datetime.strptime(event.start, '%Y-%m-%d %H:%M:%S').day,
                "type": _rrule_type,
                "index": "first",
                "month": datetime.strptime(event.start, '%Y-%m-%d %H:%M:%S').month,
                "interval": event.interval,
                "firstDayOfWeek": "sunday",
            }
        else:
            if event.month_by == "day":
                ks_by_day = {
                    "1": "first",
                    "2": "second",
                    "3": "third",
                    "4": "fourth",
                    "5": "fifth",
                    "-1": "last",
                }
                _rrule_type = 'relativeMonthly'
                _day = {
                    "MO": "monday",
                    "TU": "tuesday",
                    "WE": "wednesday",
                    "TH": "thursday",
                    "FR": "friday",
                    "SA": "saturday",
                    "SU": "sunday",
                }
                _pattern = {
                    "daysOfWeek": [_day[event.week_list]],
                    "dayOfMonth": 0,
                    "type": _rrule_type,
                    "index": ks_by_day[event.byday],
                    "month": 0,
                    "interval": event.interval,
                    "firstDayOfWeek": "sunday",
                }
            else:
                _rrule_type = "absoluteMonthly"
                _pattern = {
                    "dayOfMonth": event.day,
                    "type": _rrule_type,
                    "index": "first",
                    "month": 0,
                    "interval": event.interval,
                    "firstDayOfWeek": "sunday",
                }

        if event.end_type == "count":
            if event.rrule_type == "daily":
                occur = event.count
                interval = event.interval
                _ks_end_date = (datetime.strptime(event.stop, '%Y-%m-%d %H:%M:%S') +
                                relativedelta(days=occur * interval - 1)).date()
            elif event.rrule_type == "weekly":
                _final_date = self.env['calendar.event'].search([('id', '=', event.id)])[0].stop
                _ks_end_date = datetime.strptime(_final_date, '%Y-%m-%d %H:%M:%S').date()

            elif event.rrule_type == "monthly":
                _final_date = self.env['calendar.event'].search([('id', '=', event.id)])[0].stop
                _ks_end_date = datetime.strptime(_final_date, '%Y-%m-%d %H:%M:%S').date()
            else:
                _ks_end_date = datetime.strptime(event.start_date, '%Y-%m-%d') + \
                               relativedelta(years=(event.interval * (event.count - 1)))
        else:
            _ks_end_date = event.final_date

        ks_recurrence = {
            "pattern": _pattern,
            "range": {
                "type": "noEnd" if event.ks_rec_type_noend else "endDate",
                "recurrenceTimezone": fields.Datetime.context_timestamp(self, datetime.now()).tzinfo.zone,
                "endDate": "0001-01-01" if event.ks_rec_type_noend else str(_ks_end_date).split(' ')[0],
                "startDate": event.start.split(' ')[0],
                "numberOfOccurrences": 0,
            }
        }
        return ks_recurrence

    def ks_datetime_from_utc_to_local(self, utc_datetime):
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz(fields.Datetime.context_timestamp(self, datetime.now()).tzinfo.zone)
        utc = utc_datetime.replace(tzinfo=from_zone)
        local = utc.astimezone(to_zone)
        utcoffset = fields.Datetime.context_timestamp(self, datetime.now()).tzinfo._utcoffset.__str__().replace(":",
                                                                                                                "")[:-2]
        local = local.__str__().split(' ')[0] + "T" + local.__str__().split(' ')[1].split('+')[0] + ".0000" + utcoffset
        return local

    def ks_get_alarm_id(self, ks_e):
        alarm_id = None
        if ks_e['isReminderOn']:
            remind_min = ks_e['reminderMinutesBeforeStart']
            alarm_id = self.env['calendar.alarm'].search([('duration_minutes', '=', remind_min)])
            if not alarm_id:
                days_duration = int(ks_e['reminderMinutesBeforeStart'] / (60 * 24))
                if days_duration > 0:
                    # Here we force the 'notification' mode and not 'email' because too much emails are sent and not necessary
                    ks_vals = {
                        "name": str(days_duration) + " Day(s)",
                        "interval": "days",
                        "duration": days_duration,
                        'type': 'notification',
                    }
                    self.env['calendar.alarm'].create(ks_vals)
                else:
                    hours_duration = int(ks_e['reminderMinutesBeforeStart'] / (60))
                    if hours_duration > 0:
                        ks_vals = {
                            "name": str(hours_duration) + " Hour(s)",
                            "interval": "hours",
                            "duration": hours_duration
                        }
                        self.env['calendar.alarm'].create(ks_vals)

            alarm_id = self.env['calendar.alarm'].search([('duration_minutes', '=', remind_min)])
        return alarm_id

    def ks_get_event_start_date(self, ks_e):
        _ks_start = ks_e['start']['dateTime'].split('T')[0] + " " + ks_e['start']['dateTime'].split('T')[1].split('.')[
            0]
        ks_start = datetime.strptime(_ks_start, '%Y-%m-%d %H:%M:%S')
        return ks_start

    def ks_get_event_stop_date(self, ks_e):
        _end = ks_e['end']['dateTime']
        _end_date = ks_e['end']['dateTime'].split('T')[0]
        _end_time = ks_e['end']['dateTime'].split('T')[1].split('.')[0]
        _ks_end = _end_date + " " + _end_time
        ks_end = datetime.strptime(_ks_end, '%Y-%m-%d %H:%M:%S') + relativedelta(seconds=-1)
        return ks_end

    def ks_get_event_locations(self, ks_e):
        ks_location = ""
        for loc in ks_e['locations']:
            if ks_location == "":
                ks_location = loc['displayName']
            else:
                ks_location += "," + loc['displayName']
        return ks_location

    def ks_get_odoo_locations(self, ks_e):
        if ks_e.location:
            odoo_locations = ks_e.location.split(",")
            office365_locations = []
            for ol in odoo_locations:
                office365_locations.append({"displayName": ol})

            return office365_locations
        else:
            return ""

    def ks_get_office365_attendees(self, ks_e):
        current_user_in_partner = self.env['res.partner'].search([('email', '=', self.email)])
        if len(ks_e['attendees']):
            office365_attendees_id = current_user_in_partner.ids
            existing_odoo_attendee_emails = [oe.email for oe in self.env['res.partner'].search([])]
            for att in ks_e['attendees']:
                att_data = att['emailAddress']
                attendee_name = att_data['name']
                attendee_address = att_data['address']

                if attendee_address in existing_odoo_attendee_emails:
                    attendee = self.env['res.partner'].search([('email', '=', attendee_address)])

                    if attendee.ids[0] not in office365_attendees_id:
                        for att_id in [att for att in attendee.mapped('id')]:
                            office365_attendees_id.append(att_id)
                else:
                    ks_vals = {
                        "name": attendee_name,
                        "email": attendee_address
                    }
                    attendee = self.env['res.partner'].create(ks_vals)
                    if attendee.id not in office365_attendees_id:
                        office365_attendees_id.append(attendee.id)

            office365_attendees = self.env['res.partner'].search([('id', 'in', office365_attendees_id)])
            return office365_attendees
        return current_user_in_partner[0]

    def ks_run_calendar_import_cron_functions(self):
        for user in self.env['res.users'].search([]):
            if 'Portal' not in user.groups_id.mapped('name'):
                if not user.ks_auth_token:
                    user.ks_create_log("calendar", user.name, "", 0, datetime.now(), "office_to_odoo",
                                       "authentication", "failed",
                                       _(
                                           "Generate Authentication Token. '%s\' has not generated token yet." % user.name))
                    continue
                user.ks_get_events()

    def ks_run_calendar_export_cron_functions(self):
        for user in self.env['res.users'].search([]):
            if 'Portal' not in user.groups_id.mapped('name'):
                if not user.ks_auth_token:
                    user.ks_create_log("calendar", user.name, "", 0, datetime.now(), "odoo_to_office",
                                       "authentication", "failed",
                                       _(
                                           "Generate Authentication Token. '%s\' has not generated token yet." % user.name))
                    continue
                user.ks_post_events(q_context=None)
