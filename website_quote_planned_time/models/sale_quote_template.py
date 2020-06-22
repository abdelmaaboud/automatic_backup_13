# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class SaleQuoteLine(models.Model):
    _inherit = 'sale.quote.line'

    planned_hours = fields.Float(string='Initial Planned Hours')

    @api.onchange('product_uom_qty')
    def product_uom_qty_change(self):
        if self.product_id.type == 'service' and self.product_id.track_service == 'task':
            self.planned_hours = self.product_id.planned_hours * self.product_uom_qty

    @api.onchange('product_id')
    def _onchange_product_id(self):
        res = super(SaleQuoteLine, self).on_change_product_id()
        product_obj = self.env['product.product'].browse(self.product_id.id)
        if product_obj.type == 'service' and product_obj.track_service == 'task':
            vals = res['value']
            vals.update({
                'planned_hours': product_obj.planned_hours
            })
            res = {'value': vals, 'domain': res['domain']}
        
        return res

    """def product_uom_change(self, cr, uid, ids, product, uom_id, context=None):
        context = context or {}
        if not uom_id:
            return {'value': {'price_unit': 0.0, 'uom_id': False}}
        return self.on_change_product_id(cr, uid, ids, product, uom_id=uom_id, context=context)
    """
    