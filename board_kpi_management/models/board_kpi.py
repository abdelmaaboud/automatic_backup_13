# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
from odoo import tools

from datetime import datetime, timedelta
from calendar import monthrange
import logging
import time
import dateutil
from pytz import timezone
from dateutil.relativedelta import relativedelta
import statistics

_logger = logging.getLogger(__name__)

class BoardKPI(models.Model):
    """
    KPI
    """
    _name = 'board.kpi'
    _description = 'KPI'
    _order = 'sequence'

    @api.model
    def _method_selection(self):
        selection = []
        selection.append(('kpi_quantity', '# of KPIs'))
        selection.append(('code', 'Code'))
        return selection

    name = fields.Char(string="Name", required=True)
    category_id = fields.Many2one('board.kpi.category', string="Category")
    last_value_text = fields.Char(string="Last value", compute='_compute_last_value_text')
    last_compute_date = fields.Datetime(string="Last compute date", compute='_compute_last_value_text')
    user_ids = fields.Many2many('res.users', string="Users", required=True, help="Used for sending recurring mails and security")
    value_type = fields.Selection([('number', 'Number'), ('percentage', 'Percentage'), ('bool', 'Boolean')], string="Value type", required=True)
    value_method = fields.Selection(_method_selection, string="Computation method", required=True)
    value_ids = fields.One2many('board.kpi.value', 'kpi_id', string="Values")
    method_code = fields.Text(string="Python code")
    compute_recurring_interval = fields.Integer(string="Compute every", required=True, default=1)
    compute_recurring_type = fields.Selection([('minute', 'Minute(s)'), ('hour', 'Hour(s)'), ('day', 'Day(s)'), ('week', 'Week(s)'), ('month', 'Month(s)'), ('year', 'Year(s)')], string="Recurrency interval", required=True)
    sequence = fields.Integer('Sequence')
    enable_agregation = fields.Boolean(string='Enable values agregation', help="Allows to summarise values which aren't interesting anymore in one significant value for a period")
    agregation_period_interval = fields.Selection([('1', '1'), ('2', '2')], string="Period interval")
    agregation_period = fields.Selection([('day', 'Day(s)'), ('week', 'Week(s)'), ('month', 'Month(s)'), ('year', 'Year(s)')], string="Period")
    agregation_type = fields.Selection([('average', 'Average'), ('median', 'Median'), ('sum', 'Sum')], string="Type")
    last_agregation_date = fields.Datetime(default=time.strftime('2000-01-01 11:11:11'))
    enable_recurring_mails = fields.Boolean(string='Enable recurring mails', help="Allows you to receive recurring mails when a certain value reaches a threshold or just to receive a summary of values")
    enable_threshold_mails = fields.Boolean(string='Enable threshold mails', help="Mail with the KPI name for which threshold has been reached")
    enable_summary_mails = fields.Boolean(string='Enable summary mails', help="Mail with average, minimum and maximum in values for selected frequency")
    threshold_value = fields.Float(string="Threshold value")
    threshold_operator = fields.Selection([('>=', '>='), ('<=', '<=')], string="Threshold operator")
    threshold_reached = fields.Boolean()
    summary_mail_frequency = fields.Selection([('day', 'Every day'), ('week', 'Every monday'), ('month', 'Every first day of month'), ('year', 'Every first day of year')], string="Mail frequency", help="Each frequence will receive mail at 8:30")
    exists_summary_values = fields.Boolean()
    send_summary_mail = fields.Boolean()
    
    @api.onchange('enable_recurring_mails')
    def _reset_mail_checkboxes(self):
        self.enable_threshold_mails = False
        self.enable_summary_mails = False
    
    @api.depends('value_ids')
    def _compute_last_value_text(self):
        for kpi in self:
            if len(kpi.value_ids) == 0:
                kpi.last_value_text = 'no value computed'
            else:
                last_value = kpi.value_ids[0] # get the most recent, they are sorted in create_date desc
                kpi.last_compute_date = last_value.create_date
                if kpi.value_type == 'number':
                    kpi.last_value_text = str(last_value.value)
                elif kpi.value_type == 'percentage':
                    kpi.last_value_text = str(last_value.value) + "%"
                elif kpi.value_type == 'bool':
                    kpi.last_value_text = "Pass" if last_value.value_boolean else "Fail"

    @api.model
    def _get_eval_context(self, kpi):
        """ evaluation context to pass to safe_eval """
        return {
            'self': kpi,
            'uid': self._uid,
            'user': self.env.user,
            'time': time,
            'datetime': datetime,
            'dateutil': dateutil,
            'timezone': timezone,
        }
    
    @api.multi
    def action_compute_value(self):
        for kpi in self:
            if kpi.value_method == 'kpi_quantity':
                # compute the number of KPI
                new_value = self.env['board.kpi.value'].create({
                    'kpi_id': kpi.id,
                    'value': len(self.env['board.kpi'].search([])),
                })
            elif kpi.value_method == 'code' and kpi.method_code:
                context = self._get_eval_context(kpi)
                try:
                    tools.safe_eval(kpi.method_code.strip(), context, mode="exec", nocopy=True)
                except Exception as e:
                    raise ValidationError("Wrong python code:" + str(e))

    @api.model
    def cron_compute_kpi(self):
        current_date = time.strftime('%Y-%m-%d %H:%M:%S')
        kpi_ids = self.search([])
        for kpi in kpi_ids:
            # Test if interval passed since last kpi computation
            # compute delta from today and rule frequency
            last_kpi_computation_date = datetime.strptime(current_date, '%Y-%m-%d %H:%M:%S')
            interval = kpi.compute_recurring_interval
            if kpi.compute_recurring_type == 'minute':
                new_date = last_kpi_computation_date - relativedelta(minutes=+interval)
            if kpi.compute_recurring_type == 'hour':
                new_date = last_kpi_computation_date - relativedelta(hours=+interval)
            elif kpi.compute_recurring_type == 'day':
                new_date = last_kpi_computation_date - relativedelta(days=+interval)
            elif kpi.compute_recurring_type == 'week':
                new_date = last_kpi_computation_date - relativedelta(weeks=+interval)
            elif kpi.compute_recurring_type == 'month':
                new_date = last_kpi_computation_date - relativedelta(months=+interval)
            elif kpi.compute_recurring_type == 'year':
                new_date = last_kpi_computation_date - relativedelta(years=+interval)

            if len(kpi.value_ids) > 0:
                last_kpi_value = kpi.value_ids[0]
                if last_kpi_value.create_date >= new_date.strftime('%Y-%m-%d %H:%M:%S'):
                    continue

            kpi.action_compute_value()
        self._cron_agregate_kpi() # called here because agregation needs to run every minute too
        self._cron_recurring_mails_for_threshold() # called here because recurring mails for threshold needs to run every minute too
    
    @api.multi
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "%s (%s)" % (record.name, record.last_value_text)))
        return result
    
    """
    Next part concerns values agregation
    """
    def _check_period_interval_to_run_agregation_cron(self, kpi, current_date):
        last_agregation_date = datetime.strptime(kpi.last_agregation_date, '%Y-%m-%d %H:%M:%S')
        if last_agregation_date.month == 1 and last_agregation_date.year == 2000: # still no agregation done for current kpi
            kpi.last_agregation_date = str(current_date)
            last_agregation_date = current_date
        if kpi.agregation_period == 'day':
            if (last_agregation_date + timedelta(days=int(kpi.agregation_period_interval))) >= current_date:
                return False
        elif kpi.agregation_period == 'week':
            if (last_agregation_date + timedelta(weeks=int(kpi.agregation_period_interval))) >= current_date:
                return False
        elif kpi.agregation_period == 'month':
            if (last_agregation_date + timedelta(months=int(kpi.agregation_period_interval))) >= current_date:
                return False
        elif kpi.agregation_period == 'year':
            if (last_agregation_date + timedelta(years=int(kpi.agregation_period_interval))) >= current_date:
                return False
        return True
    
    def _handle_agregation_period(self, kpi, current_date):
        interval = int(kpi.agregation_period_interval)
        if kpi.agregation_period == 'day':
            start_date = current_date - relativedelta(days=+interval, hour=0, minute=0, second=0)
            end_date = current_date - relativedelta(days=+interval, hour=23, minute=59, second=59)
        elif kpi.agregation_period == 'week':
            date_in_week = current_date - relativedelta(weeks=+interval)
            start_date = date_in_week.replace(hour=0, minute=0, second=0) - timedelta(days=date_in_week.weekday()) # monday date of the week
            end_date = start_date.replace(hour=23, minute=59, second=59) + timedelta(days=4) # friday date of the week
        elif kpi.agregation_period == 'month':
            date_in_month = current_date - relativedelta(months=+interval)
            days_in_month = monthrange(date_in_month.year, date_in_month.month)[1]
            start_date = date_in_month.replace(day=1, hour=0, minute=0, second=0)
            end_date = date_in_month.replace(day=days_in_month, hour=23, minute=59, second=59)
        elif kpi.agregation_period == 'year':
            date_in_year = current_date - relativedelta(years=+interval)
            start_date = date_in_year.replace(day=1, month=1, hour=0, minute=0, second=0)
            end_date = date_in_year.replace(day=31, month=12, hour=23, minute=59, second=59)
        return [str(start_date), str(end_date)]
    
    def _handle_agregation_operation(self, kpi, start_date, end_date):
        # do operation (sum, average, median) on values
        kpi_values = self.env['board.kpi.value'].sudo().search([('custom_create_date', '>=', start_date), ('custom_create_date', '<=', end_date), ('kpi_id', '=', kpi.id)]).mapped('value')
        if kpi.agregation_type == 'average':
            return "{:.2f}".format(statistics.mean(kpi_values))
        elif kpi.agregation_type == 'sum':
            return sum(kpi_values)
        elif kpi.agregation_type == 'median':
            return statistics.median(kpi_values)
    
    def _cron_agregate_kpi(self):
        current_date = datetime.now()
        kpi_ids = self.sudo().search([])
        for kpi in kpi_ids:
            if kpi.enable_agregation and len(kpi.value_ids) > 0 and self._check_period_interval_to_run_agregation_cron(kpi, current_date) == True:
                result = self._handle_agregation_period(kpi, current_date)
                start_date = result[0]
                end_date = result[1]
                
                data_ids = self.env['board.kpi.value'].sudo().search([('custom_create_date', '>=', start_date), ('custom_create_date', '<=', end_date), ('kpi_id', '=', kpi.id)]) # get kpi data in specified period
                
                if len(data_ids) > 0:
                    agregated_value = self._handle_agregation_operation(kpi, start_date, end_date) # store agregated_value before deleting values
                    last_kpi_value_creation_date = data_ids[0].custom_create_date # store last kpi value creation date before deleting it
                    self.env['board.kpi.value'].sudo().search([('custom_create_date', '>=', start_date), ('custom_create_date', '<=', end_date), ('kpi_id', '=', kpi.id)]).unlink() # delete values which have been agregated from DB
                    self.env['board.kpi.value'].create({'kpi_id': kpi.id, 'value': agregated_value, 'custom_create_date': last_kpi_value_creation_date, 'agregation_type': kpi.agregation_type.title()}) # store agregated value in DB with date of last kpi value

    """
    Next part concerns recurring mails for value threshold
    """
    def _handle_threshold_mails(self, kpi):
        kpi_values = self.env['board.kpi.value'].sudo().search([('agregation_type', '=', 'Not agregated'), ('kpi_id', '=', kpi.id)], limit=2, order='custom_create_date desc').mapped('value')
        
        if kpi.enable_threshold_mails and len(kpi_values) > 0:
            if kpi.threshold_operator == '>=':
                if kpi_values[0] >= kpi.threshold_value and kpi_values[1] >= kpi.threshold_value:
                    kpi.threshold_reached = False
                elif kpi_values[0] >= kpi.threshold_value and kpi_values[1] < kpi.threshold_value:
                    kpi.threshold_reached = True
                else: # last value doesn't reach threshold
                    kpi.threshold_reached = False
            elif kpi.threshold_operator == '<=':
                if kpi_values[0] <= kpi.threshold_value and kpi_values[1] <= kpi.threshold_value: # allows to not spam recipients
                    kpi.threshold_reached = False
                elif kpi_values[0] <= kpi.threshold_value and kpi_values[1] > kpi.threshold_value: # last value doesn't reach threshold
                    kpi.threshold_reached = True
                else: # last value doesn't reach threshold
                    kpi.threshold_reached = False

            if kpi.threshold_reached:
                template_id = kpi.env.ref('board_kpi_management.kpi_value_threshold_mail_template') 
                if template_id:
                    template_id.sudo().send_mail(kpi.id, force_send=True)
    
    def _cron_recurring_mails_for_threshold(self):
        current_date = datetime.now()
        kpi_ids = self.sudo().search([])
        for kpi in kpi_ids:
            if kpi.enable_recurring_mails:
                self._handle_threshold_mails(kpi) # send threshold mails if enable
                        
    def generate_threshold_mail_values(self):
        return ';'.join(user.email for user in self.user_ids)
    
    """
    Next part concerns recurring mails for values summary
    """
    def _check_frequency_reached_to_send_mail(self, kpi, current_date):
        if kpi.summary_mail_frequency == 'day':
            if current_date.hour == 7 or current_date.minute == 30: # every day at 8:30
                return True
        elif kpi.summary_mail_frequency == 'week':
            if current_date.weekday() == 0 and current_date.hour == 7 and current_date.minute == 30: # every monday at 8:30
                return True
        elif kpi.summary_mail_frequency == 'month':
            if current_date.day == 1 and current_date.hour == 7 and current_date.minute == 30: # every first day of month at 8:30
                return True
        elif kpi.summary_mail_frequency == 'year':
            if current_date.day == 1 and current_date.month == 1 and current_date.hour == 7 and current_date.minute == 30: # every first day of year at 8:30
                return True
        return False
    
    def _handle_sending_summary_mail_frequency(self, kpi, current_date):
        if kpi.summary_mail_frequency == 'day':
            start_date = current_date - relativedelta(days=+1, hour=0, minute=0, second=0)
            end_date = current_date - relativedelta(days=+1, hour=23, minute=59, second=59)
        elif kpi.summary_mail_frequency == 'week':
            date_in_previous_week = current_date - relativedelta(weeks=+1)
            start_date = date_in_previous_week.replace(hour=0, minute=0, second=0) - timedelta(days=date_in_previous_week.weekday()) # monday date for the week
            end_date = start_date.replace(hour=23, minute=59, second=59) + timedelta(days=4) # friday date for the week
        elif kpi.summary_mail_frequency == 'month':
            date_in_previous_month = current_date - relativedelta(months=+1)
            days_in_month = monthrange(date_in_previous_month.year, date_in_previous_month.month)[1]
            start_date = date_in_previous_month.replace(day=1, hour=0, minute=0, second=0)
            end_date = date_in_previous_month.replace(day=days_in_month, hour=23, minute=59, second=59)
        elif kpi.summary_mail_frequency == 'year':
            date_in_previous_year = current_date - relativedelta(years=+1)
            start_date = date_in_previous_year.replace(day=1, month=1, hour=0, minute=0, second=0)
            end_date = date_in_previous_year.replace(day=31, month=12, hour=23, minute=59, second=59)
        return [str(start_date), str(end_date)]
    
    def _handle_summary_mails(self, kpi, current_date):
        kpi.send_summary_mail = False
        if kpi.enable_summary_mails and self._check_frequency_reached_to_send_mail(kpi, current_date):
            result = self._handle_sending_summary_mail_frequency(kpi, current_date)
            data_ids = self.env['board.kpi.value'].sudo().search([('custom_create_date', '>=', result[0]), ('custom_create_date', '<=', result[1]), ('kpi_id', '=', kpi.id)]) # get kpi data for specified frequency

            if len(data_ids) > 0:
                kpi.exists_summary_values = True
            else: # case where no values exist for specified frequency
                kpi.exists_summary_values = False
            kpi.send_summary_mail = True
        
    def _get_mail_recipients_ids(self):
        return self.env['board.kpi'].sudo().search([('send_summary_mail', '=', True)]).mapped('user_ids')
    
    def cron_recurring_mails_for_summary(self):
        current_date = datetime.now()
        kpi_ids = self.sudo().search([])
        send_mail = False
        for kpi in kpi_ids:
            if kpi.enable_recurring_mails:
                self._handle_summary_mails(kpi, current_date) # handle summary mails if enable
                if send_mail == True: # avoids multiples assignation for "send_summary_mail == True" after
                    continue
                if kpi.send_summary_mail == True:
                    send_mail = True
        
        if send_mail == True: # mail(s) to be sent
            for user in self._get_mail_recipients_ids():
                template_id = self.env.ref('board_kpi_management.kpi_values_summary_mail_template')
                if template_id:
                    template_id.write({'email_to': user.email})
                    template_id.sudo().send_mail(user.id, force_send=True)

    def get_kpi_ids_by_user(self, user):
        return self.env['board.kpi'].sudo().search([('send_summary_mail', '=', True), ('user_ids', '=', user.id)])

    def generate_summary_mail_values(self, kpi):
        result = self._handle_sending_summary_mail_frequency(self, datetime.now())
        kpi_values = self.env['board.kpi.value'].sudo().search([('custom_create_date', '>=', result[0]), ('custom_create_date', '<=', result[1]), ('kpi_id', '=', kpi.id)]).mapped('value') # get kpi values for specified frequency

        min_value = 0
        max_value = 0
        values_average = 0
        if len(kpi_values) > 0:
            min_value = min(kpi_values)
            max_value = max(kpi_values)
            values_average = "{:.2f}".format(statistics.mean(kpi_values))

        start_date = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S.%f').strftime('%d/%m/%y')
        end_date = datetime.strptime(result[1], '%Y-%m-%d %H:%M:%S.%f').strftime('%d/%m/%y')
            
        return [min_value, max_value, values_average, start_date, end_date]
