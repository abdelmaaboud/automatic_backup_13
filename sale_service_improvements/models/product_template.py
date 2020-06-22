# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = ['product.template']

    planned_hours = fields.Float(string='Initial Planned Hours')
