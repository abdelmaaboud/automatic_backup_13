# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
import datetime
from datetime import date

import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    cancel_date = fields.Date(string="Cancellation Date")
    
    
    @api.model
    def _send_email(self, so_user_set):
        """
        Sends an email to a user containing his expired sale orders
        """
        
        context = self._context.copy()
        context['so_list'] = so_user_set
        
        template = self.env['ir.model.data'].get_object('sale_order_expiration_reminder', 'email_template_sale_order_expiration')
        template = template.with_context(context)
        
        template.send_mail(so_user_set[0].id)
    
    
    @api.model
    def _send_emails(self, so_expired_set):
        """
        Sorts sale orders by user & sends an email to each user
        """
        
        so_sorted_set = {}
        for so in so_expired_set:
            if not so.user_id.email in so_sorted_set:
                so_sorted_set[so.user_id.email] = []
            so_sorted_set[so.user_id.email].append(so)
        
        for email in so_sorted_set:
            self._send_email(so_sorted_set[email])
    

    @api.model
    def _manage_cancel(self, so_expired_set):
        """
        Sets cancel_date and cancels expired sale orders that remain untouched for too long
        """
        
        now = datetime.datetime.now()
        
        for so in so_expired_set:
            config_value = self.env['sale.config.settings'].search([])
            config_value = reduce(lambda e1, e2: e1 if e1.id>e2.id else e2, config_value)
            
            cancel_date_datetime = max(
                datetime.datetime.strptime(so.validity_date, '%Y-%m-%d'),
                datetime.datetime.strptime(so.write_date, '%Y-%m-%d %H:%M:%S')
            ) + datetime.timedelta(days=config_value.sale_order_cancel_delay)
            
            so.cancel_date = cancel_date_datetime.strftime('%Y-%m-%d')
            
            if now > cancel_date_datetime:
                so.action_cancel()
    

    @api.model
    def _get_so_expired_set(self):
        """
        Generates the set of expired sale orders
        """
        
        return self.env['sale.order'].search([
            '&',
                ('state', '=', 'sent'),
                ('validity_date', '<', datetime.datetime.now().strftime('%Y-%m-%d'))
        ])    
    
    @api.model
    def _sale_order_expiration_check(self):
        """
        Cron main routine
        Extracts expired sale orders
        """

        self._manage_cancel(self._get_so_expired_set())
        self._send_emails(self._get_so_expired_set())
