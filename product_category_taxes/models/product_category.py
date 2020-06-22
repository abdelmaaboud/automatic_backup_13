# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductCategory(models.Model):
    _inherit = 'product.category'

    taxes_id = fields.Many2many(
        'account.tax', 'product_category_taxes_rel', 'category_id', 'tax_id', string="Customer Taxes",
        domain=[('type_tax_use', '!=', 'purchase')],
        help="When you set the product category for your product, these taxes will be copied to the product customer taxes."
    )
    supplier_taxes_id = fields.Many2many(
        'account.tax', 'product_category_supplier_taxes_id', 'category_id', 'tax_id', string="Vendor Taxes",
        domain=[('type_tax_use', '!=', 'sale')],
        help="When you set the product category for your product, these taxes will be copied to the product vendor taxes."
    )
    product_template_ids = fields.One2many('product.template', 'categ_id', string="Products Templates")

    @api.multi
    def write(self, vals):
        old_category_taxes = dict()
        if vals.get('taxes_id') or vals.get('supplier_taxes_id'):
            old_category_taxes.update({
                'taxes_ids': self.taxes_id.ids,
                'supplier_taxes_ids': self.supplier_taxes_id.ids,
            })
        res = super(ProductCategory, self).write(vals)
        if old_category_taxes:
            for product_template in self.product_template_ids:
                product_template.with_context(old_category_taxes=old_category_taxes).write({'categ_id': self.id})
        return res
