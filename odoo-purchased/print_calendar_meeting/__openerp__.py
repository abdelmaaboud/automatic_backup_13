# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.

{
    'name': 'Print Calendar Meetings',
    'version': '1.1',
    'price': 50.0,
    'live_test_url': 'https://youtu.be/BDGD9snRrrM',
    'currency': 'EUR',
    'license': 'Other proprietary',
    'category': 'Reporting',
    'summary': 'Print Personal & Shared Calendar Meetings',
    'description': """
        Print Calendar Meeting Report
            - Add wizard calendar meeting
              - select the start date, end date and enter user name and who attend the meeting
                and print the report
Tags:
Print meetings
Print calendar
Calendar meetings
Print customer meetings
customer meetings
print calendar
print meeting
print events
print event
print report
report calendar
report meetings
attendance
print attendance
print meeting notes
print calendar meeting
meeting minutes
print meeting minutes
print calendar minutes
calendar print
calendar meetings


            """,
    'author': 'Probuse Consulting Service Pvt. Ltd.',
    'website': 'www.probuse.com',
    'depends': ['calendar', 'web'],
    'data': ['wizard/calendar_meeting.xml',
             'report/report_reg.xml',
             'report/report_calendar_meeting.xml',
             'views/template.xml'
             ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
    'installable': True,
    'application': False,
    
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
