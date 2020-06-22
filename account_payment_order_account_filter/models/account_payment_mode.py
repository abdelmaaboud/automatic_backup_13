# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class AccountPaymentMode(models.Model):
    """This corresponds to the object payment.mode of v8 with some
    important changes"""
    _inherit = "account.payment.mode"

    default_account_ids = fields.Many2many('account.account', string="Default Accounts for Filter")
