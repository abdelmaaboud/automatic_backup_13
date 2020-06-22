# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def _get_new_taxes(self, categ_id, old_category_taxes=None):
        new_category = self.env['product.category'].browse(categ_id)
        new_taxes = {
            'taxes_id': [(4, new_tax) for new_tax in new_category.taxes_id.ids],
            'supplier_taxes_id': [(4, new_tax) for new_tax in new_category.supplier_taxes_id.ids]
        }
        if old_category_taxes:
            new_taxes['taxes_id'] += [(3, old_tax) for old_tax in old_category_taxes['taxes_ids'] if
                                      (4, old_tax) not in new_taxes['taxes_id']]
            new_taxes['supplier_taxes_id'] += [(3, old_tax) for old_tax in old_category_taxes['supplier_taxes_ids'] if
                                               (4, old_tax) not in new_taxes['supplier_taxes_id']]
        return new_taxes

    @api.model
    def create(self, vals):
        if vals.get('categ_id'):
            new_taxes = self._get_new_taxes(vals['categ_id'])
            vals['taxes_id'] = new_taxes['taxes_id']
            vals['supplier_taxes_id'] = new_taxes['supplier_taxes_id']
        return super(ProductTemplate, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('categ_id'):
            old_category_taxes = self.env.context.get('old_category_taxes')
            if not old_category_taxes:
                old_category_taxes = {
                    'taxes_ids': self.categ_id.taxes_id.ids,
                    'supplier_taxes_ids': self.categ_id.supplier_taxes_id.ids,
                }
            new_taxes = self._get_new_taxes(vals['categ_id'], old_category_taxes)
            vals.update(new_taxes)
        return super(ProductTemplate, self).write(vals)
