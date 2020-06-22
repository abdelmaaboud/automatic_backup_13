from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _

from datetime import datetime, timedelta

import logging

_logger = logging.getLogger(__name__)

class SaleSubscription(models.Model):
    _inherit = "sale.subscription"

    @api.model
    def cron_account_analytic_account(self):
        today = fields.Date.today()
        next_month = fields.Date.to_string(fields.Date.from_string(today) + relativedelta(months=1))

        # set to pending if date is in less than a month
        domain_pending = [('date', '<', next_month), ('state', '=', 'open')]
        subscriptions_pending = self.search(domain_pending)
        subscriptions_pending.write({'state': 'pending'})

        # set to pending also if date is passed
        domain_close = [('date', '<', today), ('state', 'in', ['pending', 'open'])]
        subscriptions_close = self.search(domain_close)
        subscriptions_close.write({'state': 'pending'})

        return dict(pending=subscriptions_pending.ids, closed=subscriptions_close.ids)
    
    # @api.model
    # def cron_sale_subscription_expiring(self):
        
    #     sale_subscription_ids = self.env['sale.subscription'].search([('state', 'in', ['draft', 'open']), 
    #                                           ('date', '!=', False), 
    #                                           ('date', '<', (datetime.datetime.now() + datetime.timedelta(30)).strftime("%Y-%m-%d"))
    #                                           ])
        
    #     for sale_subscription_id in sale_subscription_ids:
    #         _, template_id = self.env['ir.model.data'].get_object_reference('sale_subscription', 'email_payment_close')
    #         template = self.env['mail.template'].browse(template_id)
    #         template.send_mail(sale_subscription_id.id)
        
    #     return True
    
    @api.model
    def cron_sale_subscription_expiring(self):
        context = {}
        if self.env.context:
            context.update(self.env.context)

        #structure: {'user_id': {'old/new/future': {'partner_id': [account_obj()]}}}
        remind = {}

        def fill_remind(key, domain, write_to_renew=False):
            base_domain = [
                ('partner_id', '!=', False), #Customer
                ('user_id', '!=', False),    #Salesperson
                ('user_id.email', '!=', False),
            ]
            base_domain.extend(domain)

            for sale_subscription in self.search(base_domain, order='name asc'):
                if write_to_renew:
                    sale_subscription.state = 'to_renew'
                remind_user = remind.setdefault(sale_subscription.user_id.id, {})
                remind_type = remind_user.setdefault(key, {})
                remind_partner = remind_type.setdefault(sale_subscription.partner_id, []).append(sale_subscription)

        # Already expired
        fill_remind("old", [('state', 'in', ['pending'])])

        # Expires now
        fill_remind("new", [
            ('state', 'in', ['open']), '&',
            ('date', '!=', False),
            ('date', '<=', datetime.now().strftime('%Y-%m-%d'))], True)

        # Expires in less than 30 days
        fill_remind("future", [
            ('state', 'in', ['open']),
            ('date', '!=', False),
            ('date', '<', (datetime.now() + timedelta(30)).strftime("%Y-%m-%d"))])

        template_id = self.env["ir.model.data"].get_object_reference(
            'sale_subscription_improvements', 'email_subscription_expired_reminder')[1]
        template = self.env["mail.template"].browse(template_id)
        
        for user_id, data in remind.items():
            _logger.info("\n\nSUB Called")
            context["data"] = data
            self.env.context = context
            template.send_mail(user_id, force_send=True)

        return True
