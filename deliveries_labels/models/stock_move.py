# -*- coding: utf-8 -*-
from odoo import models,api


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def print_labels(self):
        return self.env.ref('deliveries_labels.stock_move_report_deliveries_labels').report_action(self.ids)
