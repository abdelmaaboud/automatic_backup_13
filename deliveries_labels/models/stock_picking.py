# -*- coding: utf-8 -*-
from odoo import models,api


class stock_delivery_labels(models.Model):
    _inherit = ['stock.picking']

    def print_labels(self):
        #report name: stock.report_deliverieslabels
        return self.env.ref('deliveries_labels.stock_report_deliveries_labels').report_action(self.id)
