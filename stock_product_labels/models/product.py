# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
import logging
from odoo import models, fields, api
from odoo.osv import osv
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)


class ProductWithStockLabel(models.Model):
    _inherit = ['product.template']

    @api.multi
    def print_labels(self):
        if len(self.product_variant_ids) < 1:
            raise osv.except_osv(
                _("There is no variant!"),
                _("Impossible to print labels while there is no variant defined"))
        table = []
        for variant in self.product_variant_ids:
            table.append(variant.id)
        return self.env.ref('stock_product_labels.product_labels').report_action(table)

    @api.multi
    def print_labels_w_stock_location(self):
        if len(self.product_variant_ids) < 1:
            raise osv.except_osv(
                _("There is no variant!"),
                _("Impossible to print labels while there is no variant defined"))
        print_ids = []
        for variant in self.product_variant_ids:
            stock_quants_ids = self.env['stock.quant'].search([('product_id', '=', variant.id)])
            if len(stock_quants_ids) > 0:
                for stock_quants_id in stock_quants_ids:
                    print_ids.append(stock_quants_id.id)
        if len(print_ids) < 1:
            raise osv.except_osv(
                _("No Variant in stock."),
                _("Impossible to print the stock location for this products because there is none in stock."
                  "Use the other button for simple labels"))

        return self.env.ref('stock_product_labels.product_labels_stock').report_action(print_ids)
