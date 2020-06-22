# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)
    
class ContractReportWizard(models.TransientModel):
    _name = 'contract.report.wizard'

    def _default_end_date(self):
        today = datetime.today()
        first = datetime(today.year, today.month, 1)
        return first + timedelta(days=-1)
    
    start_date = fields.Date(string="Start date")
    end_date = fields.Date(string="End date", default=_default_end_date)
    remove_prices = fields.Boolean(string="Remove prices")
    only_worklogs = fields.Boolean(string="Only worklogs")
    group_by_issue_and_task = fields.Boolean(string="Group by Issue/Task", default=True)
    subscription_id = fields.Many2one('sale.subscription', 'Subscription')
    
    def check_start_end_line_date(self, lineDate):
        line_date = fields.Date.from_string(lineDate)
        return self.get_start_date() <= line_date <= self.get_end_date()
    
    def get_start_date(self):
        return fields.Date.from_string(self.start_date or self.subscription_id.date_start)
        
    def get_end_date(self):
        return fields.Date.from_string(self.end_date or datetime.today())
    
    #get context from method print_timesheets_report in sale.subscription (contract_report)
    @api.multi
    def action_print(self):
        return self.env.ref('contract_report.contract_abakus').report_action(self)
        
    #get context from method action_service_report_sent in sale.subscription (contract_report)
    @api.multi
    def action_send_email(self):
        compose_form_id = self.env.context['compose_form_id']
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': self.env.context,
        }
