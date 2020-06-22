# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
import logging
from odoo import models, fields, api
import datetime

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    # Pure copy-paste of the method, except line 59
    @api.onchange('template_id')
    def onchange_template_id(self):
        if not self.template_id:
            return {}

        if self.partner_id:
            context = dict(self.env.context or {})
            context['lang'] = self.env['res.partner'].browse(self.partner_id.id).lang

        pricelist_obj = self.env['product.pricelist']

        lines = [(5,)]
        quote_template = self.env['sale.quote.template'].browse(self.template_id.id)
        for line in quote_template.quote_line:
            res = self.env['sale.order.line'].product_id_change()
            data = res.get('value', {})
            if self.pricelist_id:
                data.update(self.env['sale.order.line']._get_purchase_price(self.pricelist_id, line.product_id, line.product_uom_id, fields.Date.context_today(self)))
                uom_context = self.env.context.copy()
                uom_context['uom'] = line.product_uom_id.id
                price = pricelist_obj.price_get(line.product_id.id, 1)[self.pricelist_id.id]
            else:
                price = line.price_unit

            if 'tax_id' in data:
                data['tax_id'] = [(6, 0, data['tax_id'])]
            else:
                fpos = (self.fiscal_position_id and self.env['account.fiscal.position'].browse(self.fiscal_position_id.id)) or False
                taxes = fpos.map_tax(line.product_id.product_tmpl_id.taxes_id).ids if fpos else line.product_id.product_tmpl_id.taxes_id.ids
                data['tax_id'] = [(6, 0, taxes)]
            data.update({
                'name': line.name,
                'price_unit': price,
                'discount': line.discount,
                'product_uom_qty': line.product_uom_qty,
                'product_id': line.product_id.id,
                'product_uom': line.product_uom_id.id,
                'website_description': line.website_description,
                'state': 'draft',
                'customer_lead': self._get_customer_lead(line.product_id.product_tmpl_id),
                'planned_hours': line.planned_hours,
            })
            lines.append((0, 0, data))
        options = []
        for option in quote_template.options:
            if self.pricelist_id.id:
                uom_context = self.env.context.copy()
                uom_context['uom'] = option.uom_id.id
                price = pricelist_obj.price_get(option.product_id.id, 1)[self.pricelist_id.id]
            else:
                price = option.price_unit
            options.append((0, 0, {
                'product_id': option.product_id.id,
                'name': option.name,
                'quantity': option.quantity,
                'uom_id': option.uom_id.id,
                'price_unit': price,
                'discount': option.discount,
                'website_description': option.website_description,
            }))
        date = False
        if quote_template.number_of_days > 0:
            date = (datetime.datetime.now() + datetime.timedelta(quote_template.number_of_days)).strftime("%Y-%m-%d")
        data = {
            'order_line': lines,
            'website_description': quote_template.website_description,
            'options': options,
            'validity_date': date,
            'require_payment': quote_template.require_payment
        }
        if quote_template.note:
            data['note'] = quote_template.note
        return {'value': data}