from odoo import api, models, fields, _
import datetime, time
from dateutil.relativedelta import relativedelta

import logging
_logger = logging.getLogger(__name__)

class Subscription(models.Model):
    _inherit = 'sale.subscription'

    equipment_count = fields.Integer(compute='_compute_equipments_count')
    is_maintenance_subscription = fields.Boolean(default=False)
    maintenance_count = fields.Integer(compute='_compute_subscription_count')
    maintenance_setting_ids = fields.One2many('sale.subscription.maintenance.setting', 'subscription_id', string="Maintenance settings")
    security_check_ids = fields.One2many('security.check', 'subscription_id', string='Security Checks')
    security_check_count = fields.Integer(string="Security Checks Count", compute='_compute_security_check_count')

    @api.multi
    def _compute_security_check_count(self):
        for subscription in self:
            subscription.security_check_count = len(subscription.security_check_ids)

    @api.multi
    def _compute_equipments_count(self):
        for subscription in self:
            subscription.equipment_count = subscription.partner_id.parent_id.equipment_count if subscription.partner_id.parent_id else subscription.partner_id.equipment_count

    @api.multi
    def _compute_subscription_count(self):
        for subscription in self:
            subscription.maintenance_count = len(self.env['maintenance.request'].search([('subscription_id', '=', subscription.id)]))

    def _cron_create_maintenance_requests(self):
        current_date = time.strftime('%Y-%m-%d')

        maintenance_subscription_ids = self.search([('is_maintenance_subscription', '=', True), ('state', '=', 'open')])
        for subscription in maintenance_subscription_ids:
            for setting in subscription.maintenance_setting_ids:
                # Test if interval passed since last MR
                # compute delta from today and rule frequency
                last_maintenance_date = datetime.datetime.strptime(current_date, "%Y-%m-%d")
                interval = setting.maintenance_recurring_interval
                if setting.maintenance_recurring_rule_type == 'day':
                    new_date = last_maintenance_date - relativedelta(days=+interval)
                elif setting.maintenance_recurring_rule_type == 'week':
                    new_date = last_maintenance_date - relativedelta(weeks=+interval)
                elif setting.maintenance_recurring_rule_type == 'month':
                    new_date = last_maintenance_date - relativedelta(months=+interval)
                elif setting.maintenance_recurring_rule_type == 'year':
                    new_date = last_maintenance_date - relativedelta(years=+interval)

                # search for DONE (or NOT DONE) MO more recent than this date, if one exist, continue
                # TODO : check this search
                if len(self.env['maintenance.request'].search([('subscription_id', '=', subscription.id), ('level_id', '=', setting.maintenance_level_id.id), '|', ('request_date', '>=', new_date.strftime("%Y-%m-%d")), ('close_date', '>=', new_date.strftime("%Y-%m-%d"))])) > 0:
                    continue

                # Create a maintenance order
                maintenance_request_id = self.env['maintenance.request'].create({
                    'subscription_id': subscription.id,
                    'level_id': setting.maintenance_level_id.id,
                    'customer_id': subscription.partner_id.id,
                    'origin': subscription.code,
                })
                # if subscription.partner_id.maintenance_subscription_id else subscription.partner_id.parent_id.id,
                maintenance_request_id.prepare_maintenance_requets()

class SubscriptionMaintenanceSettings(models.Model):
    _name = 'sale.subscription.maintenance.setting'
    _description = 'Subscription Maintenance settings'

    subscription_id = fields.Many2one('sale.subscription', required=True)
    maintenance_level_id = fields.Many2one('maintenance.level', required=True)
    is_security_check = fields.Boolean(related='maintenance_level_id.is_security_check', string="Security Check")
    maintenance_recurring_rule_type = fields.Selection([('day', 'Day'), ('week', 'Week'), ('month', 'Month'), ('year', 'Year')], string='Maintenance Recurrency', required=True)
    maintenance_recurring_interval = fields.Integer(string="Repeat every", required=True, default=1)
