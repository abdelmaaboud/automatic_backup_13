# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class project_service_desk(models.Model):
    _inherit = ['project.project']

    state = fields.Selection([('draft','New'),
                                   ('open','In Progress'),
                                   ('cancelled', 'Cancelled'),
                                   ('pending','Pending'),
                                   ('close','Closed')],
                                  'Status', required=True, copy=False, default='open')
    calendar_event_ids = fields.One2many('calendar.event', 'project_id', string="Events")
    calendar_event_count = fields.Integer(string="Event count", compute='_computeeventcount')

    @api.multi
    @api.depends('calendar_event_ids')
    def _computeeventcount(self):
        for project in self:
            project.calendar_event_count = len(project.calendar_event_ids)

