from odoo import api, fields, models, _
import datetime
import logging
_logger = logging.getLogger(__name__)

class StockDate(models.Model):
    _name = "stock.quant.date"

    location_id = fields.Many2one('stock.location', string="Location")
    quantity = fields.Float('Quantity', readonly=True, compute="_compute_quantities", store=True)
    product_id = fields.Many2one('product.product', string = "Product", readonly=True)
    date = fields.Datetime(string="Inventory date", default=fields.Datetime.now)

    @api.depends(
        'location_id',
        'product_id'
    )
    def _compute_quantities(self):
        for _self in self:
            product_stock_quants = _self.product_id.stock_quant_ids
            for product_stock_quant in product_stock_quants:
                if product_stock_quant.location_id.id == _self.location_id.id:
                    _self.quantity = product_stock_quant.quantity
            move_line_ids = self.env['stock.move.line'].search([
                ('state', '=', 'done'), ('date', '>=', _self.date),('product_id', '=', _self.product_id.id)])
            for move_line_id in move_line_ids:
                if move_line_id.location_id.id == _self.location_id.id:
                    _self.quantity += move_line_id.qty_done
                if move_line_id.location_dest_id.id == _self.location_id.id:
                    _self.quantity -= move_line_id.qty_done
