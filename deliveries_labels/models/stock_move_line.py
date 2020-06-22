# -*- coding: utf-8 -*-
from odoo import models,api


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def print_label(self):
        return self.env.ref('deliveries_labels.stock_pack_operation_report_deliveries_labels').report_action(self.id)

    @api.multi
    def print_labels(self):
        return self.env.ref('deliveries_labels.stock_pack_operation_report_deliveries_labels').report_action(self.ids)
