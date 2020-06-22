# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime
from datetime import date
import pytz

import logging
_logger = logging.getLogger(__name__)


class sale_subscription_report_methods(models.Model):
    _inherit = 'sale.subscription'
    contract_report_info = fields.Char(compute='_compute_contract_report_info',string="Contract report settings", store=False)
    report_partner_id = fields.Many2one('res.partner', 'Partner for the Report')
    last_send_report_date = fields.Date(string="Last report sent date", readonly=True)
    
    report_start_date = fields.Date(string="Start date")
    report_end_date = fields.Date(string="End date")
    report_remove_prices = fields.Boolean(string="Remove prices")
    report_only_worklogs = fields.Boolean(string="Only worklogs")
    report_group_by_issue_and_task = fields.Boolean(string="Group by Issue/Task", default=True)
    
    @api.multi
    def action_service_report_sent(self):
        if not self.report_partner_id:
            raise UserError(_('Warning, no contact for the report is specified for this contract. Please, set one.'))
        else:
            template = self.env.ref('contract_report.email_template_service_report', False)
            compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
            ctx = dict(
                default_model='sale.subscription',
                default_res_id=self.id,
                default_subscription_id=self.id,
                default_use_template=bool(template),
                default_template_id=template.id,
                default_composition_mode='comment',
                compose_form_id=compose_form.id,
            )

            view_id = self.env['ir.model.data'].get_object_reference('contract_report', 'view_contract_report_wizard_send_by_email')[1]
            return {
                'name':_("Send by Email Service Report"),
                'view_mode': 'form',
                'view_id': view_id,
                'view_type': 'form',
                'res_model': 'contract.report.wizard',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': ctx,
            }

    @api.multi
    def print_timesheets_report(self):
        view_id = self.env['ir.model.data'].get_object_reference('contract_report', 'view_contract_report_wizard_print')[1]
        return {
            'name':_("Print Service Report"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'contract.report.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'account_ids': self.ids, 'default_subscription_id': self.id}
        }
    
    @api.one
    def _compute_contract_report_info(self):
        self.contract_report_info = ""
        contract_report = self.env['contract.report'].get_instance()
        self.contract_report_info = "Statistics: %s, Remove prices: %s" %(str(contract_report.statistics),str(contract_report.remove_prices))
    
    @api.model
    def format_decimal_number(self, number, point_numbers=2, separator=','):
        number_string = str(round(round(number, point_numbers+1),point_numbers))
        for x in range(0, point_numbers):
            if len(number_string[number_string.rfind('.')+1:]) < 2:
                number_string += '0'
            else:
                break        
        return number_string.replace('.',separator)
    
    @api.model    
    def decimal_to_hours(self, hoursDecimal):
        hours = int(hoursDecimal);
        minutesDecimal = ((hoursDecimal - hours) * 60);
        minutes = int(minutesDecimal);
        if minutes<10:
            minutes = "0"+str(minutes)
        else:
            minutes = str(minutes)
        hours = str(hours)
        return hours + ":" + minutes
    
    def get_line_ids(self):
        return self.analytic_account_id.line_ids.filtered(lambda a: fields.Date.from_string(self.report_start_date) <= fields.Date.from_string(a.date) <= fields.Date.from_string(self.report_end_date))

    def get_timesheets(self):
        return self.get_line_ids().filtered(lambda a: not a.move_id)

    def get_invoice_analytic_lines(self):
        return self.get_line_ids().filtered(lambda a: a.move_id)

    def get_standalone(self):
        return self.get_line_ids().filtered(lambda a: not a.move_id and not a.task_id)

    def get_master_type_ids(self):
        return list(dict.fromkeys(self.get_line_ids().mapped('task_id.master_type_id')))

    def get_tasks_of_type(self, type):
        if type:
            return self.get_line_ids().mapped('task_id').filtered(lambda t: t.master_type_id.id == type)
        return []

    def get_report_interval(self, contract_date_start, contract_date_end):
        if not contract_date_start:
            contract_date_start = fields.Date.from_string("1980-01-01")
        if not contract_date_end:
            local_tz = pytz.timezone('Europe/Brussels')
            contract_date_end = fields.Date.from_string(datetime.datetime.now(local_tz).date().strftime("%Y-%m-%d"))
        return self.format_date(str(contract_date_start)) + " - " + self.format_date(str(contract_date_end))

    def format_date(self, a_date):
        try:
            result = datetime.datetime.strptime(a_date, "%Y-%m-%d").date().strftime('%d-%m-%Y')
            return result
        except:
            return ""
