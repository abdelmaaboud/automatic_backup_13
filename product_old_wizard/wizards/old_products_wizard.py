# -*- coding: utf-8 -*-
from odoo import fields, models, api, exceptions, _
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)


class OldProductsWizard(models.TransientModel):
    _name = 'old.products.wizard'

    def default_date(self):
        now = datetime.now()
        date = datetime(now.year - 1, now.month, now.day, now.hour, now.minute, now.second)
        return datetime.strftime(date, "%Y-%m-%d %H:%M:%S")

    limit_date = fields.Datetime("Limit Date", help="All the products which have not been used since this date will be displayed", default=default_date)
    take_quote = fields.Boolean("Quotations", help="If True, the product displayed mustn't be used in quotations and in sale.order. If False, only the sale orders matters.", default=True)

    def action_open_old_products(self):
        def can_be_removed(product):
            if product:
                if product.purchase_count:
                    if self.env['purchase.order.line'].search([('product_id', 'in', p.product_variant_ids.ids), ('date_order', '>', self.limit_date)]).exists():
                        return False
                if product.sales_count:
                    domain = [('product_id', 'in', product.product_variant_ids.ids),
                              ('order_id.date_order', '>', self.limit_date)]
                    if not self.take_quote:
                        domain += [('state', '=', 'sale')]
                    if self.env['sale.order.line'].search(domain).exists():
                        return False
                return True
            else:
                return False

        products = self.env['product.template'].search(['&', '&', '&', '|', ('sale_ok', '=', True), ('purchase_ok', '=', True), ('qty_available', '=', 0.0), ('type', '!=', 'service'), ('create_date', '<=', self.limit_date)])
        final_products = self.env['product.template']
        for p in products:
            if can_be_removed(p):
                final_products |= p
        return {
            'name': "Products",
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_type': 'form',
            'view_mode': 'tree,kanban,form',
            'domain': [('id', 'in', final_products.ids)],
            'context': {},
        }


