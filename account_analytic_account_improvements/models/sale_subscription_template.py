# -*- coding: utf-8 -*-

from odoo import models, fields, api

import datetime
import logging
_logger = logging.getLogger(__name__)

class SaleSubscriptionTemplate(models.Model):
    _inherit = 'sale.subscription.template'

    invoice_contract_type = fields.Selection([('balance', 'Balanced contract (BL)'), ('fix_price', 'Fix price contract'), ('other', 'Others')], default='fix_price', string="Type of invoicing")
    contract_team = fields.Many2one('account.analytic.account.team', string="Team")
    resource_calendar_id = fields.Many2one('resource.calendar', string="Working Time")
    invoicable_factor_inside_calendar = fields.Many2one('hr_timesheet_invoice.factor', string='Default invoicable factor during calendar')
    invoicable_factor_outside_calendar = fields.Many2one('hr_timesheet_invoice.factor', string='Default invoicable factor outside calendar')

    timesheet_product = fields.Many2one('product.product', string="Timesheet product")
    timesheet_product_price = fields.Float("Hourly Rate")
    contractual_minimum_quantity = fields.Float(string="Contractual minimum quantity")
    contractual_minimum_amount = fields.Float(string="Contractual minimum amount")

    minimum_invoicable_quantity = fields.Float(string="Minimum Invoicable Quantity", default="0.25", required=True)

    description_needed = fields.Boolean(string="Description needed", default=False)
    supplier_needed = fields.Boolean(string="Supplier needed", default=False)
    subscription_start_date_needed = fields.Boolean(string="Subscription start date needed", default=False)
    subscription_end_date_needed = fields.Boolean(string="Subscription end date needed", default=False)

    use_project = fields.Boolean(string="Use Project")
    project_template_id = fields.Many2one('project.project', string="Project Template")

    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.user.company_id.currency_id)
    subscription_line_ids = fields.One2many('sale.subscription.template.line', 'template_id', string="Subscription Lines")
    recurring_total = fields.Float(string="Recurring Price")

    @api.onchange('subscription_line_ids')
    def subscription_line_change(self):
        for template in self:
            template.recurring_total = 0
            for line in template.subscription_line_ids:
                template.recurring_total += line.price_subtotal

    @api.onchange('timesheet_product')
    def timesheet_product_change(self):
        for template in self:
            if template.timesheet_product:
                template.timesheet_product_price = template.timesheet_product.lst_price
            else:
                template.timesheet_product_price = 0

    @api.onchange('timesheet_product_price', 'contractual_minimum_quantity')
    def compute_minimum_amount(self):
        for template in self:
            template.contractual_minimum_amount = template.timesheet_product_price * template.contractual_minimum_quantity

