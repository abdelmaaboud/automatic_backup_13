# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
import logging
from odoo import models, api

_logger = logging.getLogger(__name__)


class StockDeliveryLabels(models.Model):
    _inherit = ['stock.picking']

    def print_delivery_note(self, context=None):
        """ report name: stock.report_deliverieslabels """
        return self.env.ref('stock_delivery_note_report.action_report_delivery_order').report_action(self)

    @api.model
    def get_pl_out_for_partner(self):
        picking_types = self.env['stock.picking.type'].search([['code', '=', 'outgoing']])
        types = []
        for picking_type in picking_types:
            types.append(picking_type.id)
        pickings = self.env['stock.picking'].search([
            ['partner_id', '=', self.partner_id.id],
            ['picking_type_id', 'in', types],
            ['state', 'in', ['waiting', 'confirmed', 'partially_available', 'assigned']],
            ['id', '!=', self.id]
        ])
        return pickings

    @api.model
    def get_pl_data_out_for_partner(self):

        pickings = self.get_pl_out_for_partner()

        if len(pickings) > 0:
            result = []

            move_state_dict = {
                'waiting': 'Waiting Another Move',
                'confirmed': 'Waiting Avaibility',
                'assigned': 'Available',
                'done': 'Transferred',
            }
            picking_state_dict = {
                'waiting': 'Waiting Another Operation',
                'confirmed': 'Waiting Avaibility',
                'partially_available': 'Partially Available',
                'assigned': 'Ready to transfer',
            }

            for picking in pickings:
                if picking.id == self.id:
                    continue
                picking_dict = {
                    'name': picking.name,
                    'origin': picking.origin,
                }

                if picking.state in picking_state_dict:
                    picking_dict['state'] = picking_state_dict[picking.state]
                else:
                    picking_dict['state'] = picking.state

                if picking.backorder_id:
                    picking_dict['backorder'] = picking.backorder_id.name
                else:
                    picking_dict['backorder'] = False

                picking_dict['moves'] = []
                for move in picking.move_lines:
                    move_dict = {
                        'name': move.product_id.name,
                        'brand': move.product_id.product_brand_id.name,
                        'full_name': str(move.product_id.product_brand_id.name) + " - " + move.product_id.name,
                        'ean13': move.product_id.barcode,
                        'ref': move.product_id.default_code,
                        'qty': move.product_uom_qty,
                        'uom': move.product_uom.name,
                        'date': move.date,
                    }

                    if move.state in move_state_dict:
                        move_dict['state'] = move_state_dict[move.state]
                    else:
                        move_dict['state'] = move.state

                    picking_dict['moves'].append(move_dict)

                picking_dict['moves'] = sorted(picking_dict['moves'], key=lambda k: k['full_name'])
                result.append(picking_dict)

            return result
