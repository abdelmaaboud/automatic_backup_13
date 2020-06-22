from odoo import models,fields

class stock_move_transient(models.TransientModel):
    _name = "stock.move.transient"
    _description = "Scrap Moves"

    product_id = fields.Many2one('product.product', 'Product')
    product_qty = fields.Float('Quantity')
    date = fields.Datetime('Date')
    picking_id = fields.Many2one('stock.picking', 'Reference')

    def print_labels_from_stock_move_with_custom_qty(self, stock_move_id, qty):
        stock_move_obj = self.pool.get('stock.move')
        stock_move_transient_obj = self.pool.get('stock.move.transient')
        
        stock_move = stock_move_obj.browse(stock_move_id.id)
        stock_move_transient = stock_move_transient_obj.create({
            'picking_id': stock_move.picking_id.id,
            'date': stock_move.date,
            'product_id': stock_move.product_id.id,
            'product_qty': int(qty),
        })
        
        return self.env.ref('deliveries_labels.stock_move_transient_report_deliveries_labels').report_action(stock_move_transient.id)
