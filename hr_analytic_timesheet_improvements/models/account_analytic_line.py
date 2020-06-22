# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.tools.translate import _
from odoo.exceptions import UserError
import html2text


import logging
_logger = logging.getLogger(__name__)

class AnalyticAccountLine(models.Model):
    _inherit = 'account.analytic.line'

    def _get_default_date(self):
        return datetime.strftime(self.check_and_correct_date_in_fifteen_step(datetime.now()), '%Y-%m-%d %H:%M:%S')

    date_begin = fields.Datetime(string='Start Datetime', default=_get_default_date)
    flat_name = fields.Char(string="Display Name")
    task_state = fields.Many2one(related='task_id.stage_id', string="Task State")
    project_id = fields.Many2one('project.project', string="Project", default=lambda self: self._get_default_project())
    task_planned_hours = fields.Float(related='task_id.planned_hours', string="Planned time on task")
    effective_hours = fields.Float(related="task_id.effective_hours", string="Hours Spent")
    remaining_hours = fields.Float(related="task_id.remaining_hours", string="Remaining Hours")
    note_to_manager = fields.Text("Note to Manager")
    stage_id = fields.Many2one(related='task_id.stage_id')


    @api.multi
    @api.onchange('name')
    def compute_display_name(self):
        for line in self:
            if line.name:
                line.flat_name = html2text.html2text(line.name)

    @api.multi
    @api.onchange('flat_name')
    def compute_name(self):
        for line in self:
            if line.flat_name:
                line.name = line.flat_name

    def _get_default_project(self):
        if self.account_id:
            if len(self.account_id.project_ids) > 0:
                if self.account_id.project_ids[0] and self.account_id.project_ids[0].id:
                    return self.account_id.project_ids[0].id
        return False
    
    def check_and_correct_date_in_fifteen_step(self, date):
        newdate = date
        newhour = newdate.hour
        step = 0
        round = False
        minute_under_fifteen = newdate.minute
        while (minute_under_fifteen > 15):
           minute_under_fifteen = minute_under_fifteen - 15
           step+=1
        if(minute_under_fifteen>=(15/2)):
            round = True
        if round:
            newminute = (step*15)+15
            if newminute==60:
                newdate = newdate + timedelta(hours=1)
                newminute = 0
        else:
            newminute = step*15
        
        newdate = newdate.replace(minute=newminute, second=0)
        return newdate

    # set the date of date_begin to "date" to avoid inconsistency problems
    @api.multi
    @api.onchange('date_begin')
    def copy_dates(self):
        self.date = self.date_begin

    @api.multi
    def remove_quarter(self):
        for line in self:
            if line.unit_amount > 0:
                line.unit_amount = line.unit_amount - 0.25

    @api.multi
    def add_quarter(self):
        for line in self:
            line.unit_amount = line.unit_amount + 0.25

    @api.multi
    def write(self, vals):
        self._check_rights_to_write()
        if vals.get('date_begin'):
            start_date = datetime.strptime(vals.get('date_begin'), '%Y-%m-%d %H:%M:%S')
            newdate = self.check_and_correct_date_in_fifteen_step(start_date)
            if start_date.minute != newdate.minute or start_date.second != newdate.second:
                vals.update({'date_begin': datetime.strftime(newdate, '%Y-%m-%d %H:%M:%S')})
            vals.update({'date': newdate.date()})
        # Display Name
        if vals.get('name'):
            vals.update({'flat_name': html2text.html2text(vals.get('name'))})
        elif vals.get('flat_name'):
            vals.update({'name': vals.get('flat_name')})

        result = super(AnalyticAccountLine, self).write(vals)
        return result

    @api.model
    def create(self, vals):
        # No project? So get it from account analytic
        if 'project_id' not in vals:
            project_id = self.env['project.project'].search([('analytic_account_id', '=', vals['account_id'])], limit=1)
            if project_id:
                vals.update({'project_id': project_id.id})

        # Test if timesheet or not (as made in 'timesheet_grid', timesheets are only lines that are linked to a 'project_id'
        if vals.get('project_id'):
            if vals.get('date_begin'):
                start_date = datetime.strptime(vals.get('date_begin'), '%Y-%m-%d %H:%M:%S')
                newdate = self.check_and_correct_date_in_fifteen_step(start_date)
                if start_date.minute != newdate.minute or start_date.second != newdate.second:
                    start_date = self.check_and_correct_date_in_fifteen_step(start_date)
                    vals.update({'date_begin': datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')})
                    vals.update({'date': newdate.date()})
                else:
                    vals.update({'date': datetime.strftime(start_date, '%Y-%m-%d')})
            elif vals.get('date'):
                date = datetime.strptime(vals.get('date'), '%Y-%m-%d')
                date = self.check_and_correct_date_in_fifteen_step(date)
                vals.update({'date': date.date()})
                vals.update({'date_begin': datetime.strftime(date, '%Y-%m-%d %H:%M:%S')})
            else:
                date = self.check_and_correct_date_in_fifteen_step(datetime.now())
                vals.update({'date_begin': datetime.strftime(date, '%Y-%m-%d %H:%M:%S')})
                vals.update({'date': datetime.strftime(date, '%Y-%m-%d')})
        if vals.get('name'):
            vals.update({'flat_name': html2text.html2text(vals.get('name'))})
        elif vals.get('flat_name'):
            vals.update({'name': vals.get('name')})
        hr_analytic_timesheet_id = super(AnalyticAccountLine, self).create(vals)
        return hr_analytic_timesheet_id

    @api.multi
    def unlink(self):
        self._check_rights_to_write()
        return super(AnalyticAccountLine, self).unlink()

    # The following method is called when writing on the AAL
    # I will inherit it to allow the HR Manager & Account Manager
    # to edit them even if the Timesheet is confirmed
    def _check_rights_to_write(self):
        f1 = self.env.user.has_group('base.group_hr_user')
        f2 = self.env.user.has_group('account.group_account_manager')
        if not (f1 or f2):
            for line in self:
                if line.validated: #TODO check if OK
                    raise UserError(_('You cannot modify an entry in a confirmed timesheet. Only HR Officer and Account Manager can do it.'))
        return True

    @api.onchange('project_id')
    def onchange_project_id(self):
        res = super(AnalyticAccountLine, self).onchange_project_id()
        if self.project_id:
            self.account_id = self.project_id.analytic_account_id
            if res and 'domain' in res and 'task_id' in res.get('domain'):
                init_domain = res['domain']['task_id']
                res.update({
                    'domain': {
                        'task_id': init_domain + [('is_closed', '=', False)]
                    }
                })
        return res

    @api.multi
    def close_task_issue(self):
        self.ensure_one()
        if self.task_id:
            self.task_id.action_close()

    @api.multi
    def delete_worklog(self):
        self.unlink()
