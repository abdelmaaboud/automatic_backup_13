# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.onchange('cost_price_from_suppliers')
    def _onchange_cost_price_from_suppliers(self):
        if self.seller_ids and self.cost_price_from_suppliers:
            for p in self:
                p.standard_price = p.compute_lowest_supplier_price()
                if len(p.product_variant_ids) == 1:
                    p.product_variant_ids.standard_price = p.compute_lowest_supplier_price()
    
    @api.depends('cost_price_from_suppliers', 'seller_ids', 'manual_cost_price')
    def compute_lowest_supplier_price(self):
        new_price = self.manual_cost_price
        if self.cost_price_from_suppliers:
            # Get the lowest price for suppliers
            new_price = 0.0
            for supp in self.seller_ids.filtered(lambda a: a.price > 0.0):
                if (new_price == 0.0 and supp.price > 0.0) or (supp.price < new_price):
                    new_price = supp.price
        return new_price

    cost_price_from_suppliers = fields.Boolean('Auto cost from suppliers', default=True)
    manual_cost_price = fields.Float(default=0)

    @api.model
    def create(self, vals):
        res = super(ProductTemplate, self).create(vals)
        if res.seller_ids and res.cost_price_from_suppliers:
            res.standard_price = res.compute_lowest_supplier_price()
            if len(res.product_variant_ids) == 1:
                res.product_variant_ids.standard_price = res.compute_lowest_supplier_price()
        return res

    @api.multi
    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        for p in self:
            if self.seller_ids and self.cost_price_from_suppliers and 'standard_price' not in vals:
                p.standard_price = p.compute_lowest_supplier_price()
                if len(p.product_variant_ids) == 1:
                    p.product_variant_ids.standard_price = p.compute_lowest_supplier_price()
        return res