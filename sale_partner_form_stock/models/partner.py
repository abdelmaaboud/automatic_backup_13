# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
from odoo import models, fields, api, _


class PartnerWithStock(models.Model):
    _inherit = ['res.partner']

    open_deliveries_count = fields.Integer(string="Product(s) to transfer", compute="_compute_products_to_deliver")

    @api.multi
    def _compute_products_to_deliver(self):
        stock_picking_obj = self.env['stock.picking']
        stock_picking_type_obj = self.env['stock.picking.type']
        for partner in self:
            picking_ids = self.env['stock.picking'].search([
                ('partner_id', '=', partner.id),
                ('state', 'not in', ['draft', 'done', 'cancel'])
            ], order="date desc")

            nbr = 0
            for picking in picking_ids:
                for move in picking.move_lines:
                        nbr += move.product_uom_qty
                        
            partner.open_deliveries_count = nbr
