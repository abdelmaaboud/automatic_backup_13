# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions

from odoo import models, api


class ProductProductBrand(models.Model):
    _inherit = 'product.product'

    @api.multi
    def name_get(self):
        """Redefines the name_get method from product.product.
        It is the same method's body but it includes the brand."""
        result = []
        for product in self:
            result.append((product.id, product.name_get_full()))
        return result

    @api.model
    def name_get_full(self):
        full_name = ''

        # Get Brand if set
        if self.product_brand_id:
            full_name += self.product_brand_id.name + ' - '

        # Normal product name
        full_name += self.name

        # Code
        if self.default_code:
            full_name += ' [{}]'.format(self.default_code)

        return full_name
