# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

import logging

_logger = logging.getLogger(__name__)

class PickingList(models.Model):
    _inherit = ['stock.picking']

    created_sale_order_id = fields.Many2one('sale.order', string="Created SO")
    do_not_create_an_so = fields.Boolean(string="Do not create an SO for this PL")

    @api.multi
    def action_create_sale_order(self):
        sale_order_ids = []
        for picking in self:
            if picking.created_sale_order_id:
                sale_order_ids.append(picking.created_sale_order_id)
            else:
                if not picking.do_not_create_an_so:
                    # Create the SO
                    sale_order_id = self.env['sale.order'].create({
                        'partner_id': picking.partner_id.id,
                        'origin_picking_id': picking.id,
                        'picking_ids': [(4, picking.id)],
                        'client_order_ref': picking.name,
                        'internal_order_ref': picking.name,
                        'fiscal_position_id': picking.partner_id.property_account_position_id.id,
                        'payment_term_id': picking.partner_id.property_payment_term_id.id,
                    })
                    
                    picking.created_sale_order_id = sale_order_id
                    sale_order_ids.append(sale_order_id)

                    # Create the lines
                    for operation in picking.move_lines:
                        sale_order_line_id = self.env['sale.order.line'].create({
                            'order_id': sale_order_id.id,
                            'product_id': operation.product_id.id,
                            'product_uom_qty': operation.product_qty,
                            'product_uom': operation.product_uom.id,
                            'move_ids': [(4, operation.id)],
                        })

        if len(sale_order_ids) > 0:
            action = self.env.ref('sale.action_quotations').read()[0]

            if len(sale_order_ids) > 1:
                action['domain'] = [('id', 'in', sale_order_ids)]
            else:
                action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
                action['res_id'] = sale_order_ids[0].id

            return action
