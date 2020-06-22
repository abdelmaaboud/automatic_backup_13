# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT

import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = ['sale.order']

    origin_picking_id = fields.Many2one('stock.picking', string="Origin Picking List")

class SaleOrderLine(models.Model):
    _inherit = ['sale.order.line']

    origin_stock_pack_operation_id = fields.Many2one('stock.move.line', string="Origin pack operation")
    

    @api.multi
    def _action_procurement_create(self):
        """
        Create procurements based on quantity ordered. If the quantity is increased, new
        procurements are created. If the quantity is decreased, no automated action is taken.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        new_procs = self.env['procurement.order'] #Empty recordset
        for line in self:
            if line.state != 'sale' or not line.product_id._need_procurement():
                continue
            qty = 0.0
            for proc in line.procurement_ids.filtered(lambda r: r.state != 'cancel'):
                qty += proc.product_qty
            if float_compare(qty, line.product_uom_qty, precision_digits=precision) >= 0:
                continue

            if not line.order_id.procurement_group_id:
                vals = line.order_id._prepare_procurement_group()
                line.order_id.procurement_group_id = self.env["procurement.group"].create(vals)

            # If the Picking list already exists, just set groups
            if line.order_id.origin_picking_id:
                line.order_id.origin_picking_id.group_id =  line.order_id.procurement_group_id
                line.qty_delivered = line.origin_stock_pack_operation_id.product_qty
            else:
                vals = line._prepare_order_line_procurement(group_id=line.order_id.procurement_group_id.id)
                vals['product_qty'] = line.product_uom_qty - qty
                new_proc = self.env["procurement.order"].with_context(procurement_autorun_defer=True).create(vals)
                new_procs += new_proc
                new_procs.run()
        return new_procs
