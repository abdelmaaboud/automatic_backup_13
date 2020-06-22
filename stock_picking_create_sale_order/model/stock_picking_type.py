# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

import logging

_logger = logging.getLogger(__name__)

class StockPickingType(models.Model):
    _inherit = ['stock.picking.type']

    count_picking_needing_so = fields.Integer(compute='_compute_picking_needing_so_count')
    
    def _compute_picking_needing_so_count(self):
        for picking_type in self:
            picking_type.count_picking_needing_so = self.env['stock.picking'].search_count([('created_sale_order_id', '=', False), ('picking_type_id', '=', picking_type.id), ('origin', '=', False), ('group_id', '=', False), ('state', '!=', 'cancel'), ('picking_type_id.code', '=', 'outgoing'), ('do_not_create_an_so', '=', False)])

    @api.one
    def get_action_picking_tree_needing_so(self):
        return self._get_action('stock_picking_create_sale_order.action_picking_tree_needing_so')
