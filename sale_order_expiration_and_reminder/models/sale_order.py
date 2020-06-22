# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions

from datetime import datetime, timedelta
from functools import reduce
from odoo import models, fields, api


class SaleOrderExpirationReminder(models.Model):
    _inherit = 'sale.order'

    cancel_date = fields.Date(string="Cancellation Date")

    consultancy_expiration_selection = fields.Selection(selection=[
        ('not_applicable', 'Not Applicable'),
        ('in_progress', 'In Progress'),
        ('to_renew', 'To Renew'),
        ('closed', 'Closed')
    ], string='Contract Consultancy Expiration', default='not_applicable')
    consultancy_expiration_date = fields.Date()
    consultancy_expiration_in_days = fields.Integer(compute='_compute_cexpiration_in_days')

    @api.depends('consultancy_expiration_date')
    def _compute_cexpiration_in_days(self):
        """
        For consultancy: compute expiration in days
        """
        date_format = "%Y-%m-%d"
        now = datetime.now()
        for sale_order in self:
            consultancy_expiration_date = datetime.strptime(self.consultancy_expiration_date, date_format)
            date_delta = consultancy_expiration_date - now
            sale_order.consultancy_expiration_in_days = date_delta.days

    @api.model
    def _cron_so_cexpiration_reminder(self):
        """
        For consultancy: cron job sending expiration time reminder
        """
        context = {}
        if self.env.context:
            context.update(self.env.context)

        #structure: {'user_id': {'old/new/future': {'partner_id': [account_obj()]}}}
        remind = {}

        def fill_remind(key, domain, write_to_renew=False):
            base_domain = [
                ('state', '=', 'sale'),
                ('partner_id', '!=', False), #Customer
                ('user_id', '!=', False),    #Salesperson
                ('user_id.email', '!=', False),
            ]
            base_domain.extend(domain)

            for sale_order in self.search(base_domain, order='name asc'):
                if write_to_renew:
                    sale_order.consultancy_expiration_selection = 'to_renew'
                remind_user = remind.setdefault(sale_order.user_id.id, {})
                remind_type = remind_user.setdefault(key, {})
                remind_partner = remind_type.setdefault(sale_order.partner_id, []).append(sale_order)

        # Already expired
        fill_remind("old", [('consultancy_expiration_selection', 'in', ['to_renew'])])

        # Expires now
        fill_remind("new", [
            ('consultancy_expiration_selection', 'in', ['in_progress']), '&',
            ('consultancy_expiration_date', '!=', False),
            ('consultancy_expiration_date', '<=', datetime.now().strftime('%Y-%m-%d'))], True)

        # Expires in less than 30 days
        fill_remind("future", [
            ('consultancy_expiration_selection', 'in', ['in_progress']),
            ('consultancy_expiration_date', '!=', False),
            ('consultancy_expiration_date', '<', (datetime.now() + timedelta(30)).strftime("%Y-%m-%d"))])

        #For the url in  generated email linked to the sale orders list (menuitem)
        context['base_url'] = self.env["ir.config_parameter"].get_param("web.base.url")
        context['action_id'] = self.env["ir.model.data"].get_object_reference('sale', 'action_orders')[1]

        template_id = self.env["ir.model.data"].get_object_reference(
            'sale_order_expiration_and_reminder', 'sale_order_expiration_reminder_cron_mail_template')[1]
        template = self.env["mail.template"].browse(template_id)

        for user_id, data in remind.items():
            context["data"] = data
            self.env.context = context
            template.send_mail(user_id, force_send=True)

        return True

    @api.model
    def _send_email(self, so_user_set):
        """
        Sends an email to a user containing his expired sale orders
        """

        context = self._context.copy()
        context['so_list'] = so_user_set

        template = self.env['ir.model.data'].get_object('sale_order_expiration_reminder',
                                                        'email_template_sale_order_expiration')
        template = template.with_context(context)

        template.send_mail(so_user_set[0].id)

    @api.model
    def _send_emails(self, so_expired_set):
        """
        Sorts sale orders by user & sends an email to each user
        """

        so_sorted_set = {}
        for my_so in so_expired_set:
            if my_so.user_id.email not in so_sorted_set:
                so_sorted_set[my_so.user_id.email] = []
            so_sorted_set[my_so.user_id.email].append(my_so)

        for email in so_sorted_set:
            self._send_email(so_sorted_set[email])

    @api.model
    def _manage_cancel(self, so_expired_set):
        """
        Sets cancel_date and cancels expired sale orders that remain untouched for too long
        """

        now = datetime.now()

        for my_so in so_expired_set:
            config_value = self.env['sale.config.settings'].search([])
            config_value = reduce(lambda e1, e2: e1 if e1.id > e2.id else e2, config_value)

            cancel_date_datetime = max(
                datetime.strptime(my_so.validity_date, '%Y-%m-%d'),
                datetime.strptime(my_so.write_date, '%Y-%m-%d %H:%M:%S')
            ) + timedelta(days=config_value.sale_order_cancel_delay)

            my_so.cancel_date = cancel_date_datetime.strftime('%Y-%m-%d')

            if now > cancel_date_datetime:
                my_so.action_cancel()

    @api.model
    def _get_so_expired_set(self):
        """
        Generates the set of expired sale orders
        """

        return self.env['sale.order'].search([
            '&',
            ('state', '=', 'sent'),
            ('validity_date', '<', datetime.now().strftime('%Y-%m-%d'))
        ])

    @api.model
    def _sale_order_expiration_check(self):
        """
        Cron main routine
        Extracts expired sale orders
        """

        self._manage_cancel(self._get_so_expired_set())
        self._send_emails(self._get_so_expired_set())
