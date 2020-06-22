# -*- coding: utf-8 -*-
from odoo import models, api
import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def print_labels(self):
        #report name: sale.report_deliverieslabels
        return self.env.ref('deliveries_labels.sale_report_deliveries_labels').report_action(self.id)
