# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def _prepare_procurement_values(self, group_id=False):
        """ Prepare specific key for moves or other components that will be created from a procurement rule
        comming from a sale order line. This method could be override in order to add other custom key that could
        be used in move/po creation.
        """
        if not self.order_id.confirmation_date:
            self.order_id.confirmation_date = fields.Datetime.now()
        return super(SaleOrderLine, self)._prepare_procurement_values(group_id)