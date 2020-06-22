# -*- coding: utf-8 -*-

from odoo import models, fields, api

class HrTimesheetInvoiceFactor(models.Model):
    _name = 'hr_timesheet_invoice.factor'
    _description = 'Invoice Rate'

    name = fields.Char(string='Internal Name', required=True, translate=True)
    customer_name = fields.Char(string='Public Name', help="Label for the customer", translate=True)
    factor = fields.Float(string='Discount (%)', required=True, help="Discount in percentage")
