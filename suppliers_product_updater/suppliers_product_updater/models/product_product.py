# -*- coding: utf-8 -*-
from odoo import models,fields, api, _

import logging
_logger = logging.getLogger(__name__)

class ProductTeamplate(models.Model):
    _inherit = 'product.template'

    last_update_price = fields.Datetime('Last price update', readonly=True, default=0)
    total_suppliers_stock = fields.Integer(string="Total Suppliers Stock", compute='_compute_total_suppliers_stock')

    @api.multi
    def update_product_with_supplier_updater(self):
        for product in self:
            self.env['supplier.updater.setting'].search([('active', '=', True), ('demo_mode', '=', False)]).execute_updater_for_supplierinfo_ids(product.seller_ids.filtered(lambda r: r.state != 'obsolete'))

    @api.multi
    def _compute_total_suppliers_stock(self):
        for product in self:
            total = 0
            for supplier in product.seller_ids:
                total += supplier.qty_available
            product.total_suppliers_stock = total
