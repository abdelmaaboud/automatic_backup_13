from odoo import api, models, fields, _

import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    equipments_created = fields.Boolean(default=False)
    equipments_count = fields.Integer(compute='_compute_equipments_count', string='# Equipments')

    def _compute_equipments_count(self):
        for order in self:
            order.equipments_count = self.env['maintenance.equipment'].search_count([('sale_order_id', '=', order.id)])

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    equipment_ids = fields.One2many('maintenance.equipment', 'sale_order_line_id')
