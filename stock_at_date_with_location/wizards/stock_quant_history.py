from odoo import fields, models, _
from odoo.osv import expression
import logging
import datetime
_logger = logging.getLogger(__name__)

class StockQuantityHistory(models.TransientModel):
    _inherit = "stock.quantity.history"

    def _create_stock_quant_date(self):
        self.env['stock.quant.date'].sudo().search([]).unlink()
        internal_location_ids = self.env['stock.location'].search([('usage', '=', 'internal')])
        internal_location_ids_array = []
        for internal_location in internal_location_ids:
            internal_location_ids_array.append(internal_location.id)
        stock_quant_ids = self.env["stock.quant"].search([('location_id', 'in', internal_location_ids_array)])
        for stock_quant in stock_quant_ids:
            location_id = stock_quant.location_id.id
            product_id = stock_quant.product_id.id
            self.env['stock.quant.date'].sudo().create({
                'location_id': location_id,
                'product_id': product_id,
                'date': self.date
            })

    def open_table(self):
        action = super(StockQuantityHistory, self).open_table()
        if self.compute_at_date:
            self._create_stock_quant_date()
            tree_view_id = self.env.ref('stock_at_date_with_location.stock_quant_date_tree_view').id
            action = {
                'type': 'ir.actions.act_window',
                'views': [(tree_view_id, 'tree')],
                'view_mode': 'tree',
                'name': _('Products'),
                'res_model': 'stock.quant.date',
                'domain': [],
                'context': dict(to_date=self.date, search_default_by_product=1, search_default_by_location=2),
            }

        return action