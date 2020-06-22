# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class StockPickingWithCustomerSOReference(models.Model):
    _inherit = 'stock.picking'

    customer_reference = fields.Char(string="Reference/Description (from SO)", compute="_compute_customer_reference")

    @api.multi
    def _compute_customer_reference(self):
        for pick in self:
            order = self.env['sale.order'].search([
                ('partner_id', '=', pick.partner_id.id),
                ('name', '=', pick.group_id.name)])
            if len(order) > 0:
                order = order[0]
            pick.customer_reference = order.client_order_ref
