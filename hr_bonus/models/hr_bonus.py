# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
import logging
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


class Bonus(models.Model):
    _name = 'hr.bonus'
    _inherit = ['mail.thread']
    _order = 'date desc'

    name = fields.Char(copy=False, index=True, required=True, readonly=True,
                       states={'draft': [('readonly', False)]}, track_visibility='onchange')
    description = fields.Text(readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('refused', 'Refused'),
    ], default='draft', required=True, track_visibility='onchange')
    date = fields.Datetime(required=True, readonly=True, states={'draft': [('readonly', False)]})
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, readonly=True,
                                  states={'draft': [('readonly', False)]},
                                  default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1))

    @api.multi
    def action_draft(self):
        self.write({'state': 'draft'})

    @api.multi
    def action_submit(self):
        self.write({'state': 'submitted'})

    @api.multi
    def action_approve(self):
        self.write({'state': 'approved'})

    @api.multi
    def action_paid(self):
        self.write({'state': 'paid'})

    @api.multi
    def action_refuse(self):
        self.write({'state': 'refused'})

    @api.multi
    def unlink(self):
        for bonus in self:
            if bonus.state not in ('draft', 'refused'):
                raise exceptions.Warning(_('You cannot delete a Bonus which is not draft or refused. You should put it back to draft.'))
        return models.Model.unlink(self)
