from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class AccountAnalyticLine(models.Model):
    _inherit = ['account.analytic.line']

    def _get_sale_order_line_vals(self):
        order = self.env['sale.order'].sudo().search([('project_id', '=', self.account_id.id)], limit=1)
        if not order:
            return False
        if order.state not in ['sale', 'done']:
            raise Warning(_('The Sale Order %s linked to the Analytic Account must be validated before registering expenses.') % order.name)

        last_so_line = self.env['sale.order.line'].sudo().search([('order_id', '=', order.id)], order='sequence desc', limit=1)
        last_sequence = last_so_line.sequence + 1 if last_so_line else 100

        fpos = order.fiscal_position_id or order.partner_id.property_account_position_id
        taxes = fpos.map_tax(self.product_id.taxes_id)
        price = self._get_invoice_price(order)

        return {
            'order_id': order.id,
            'name': self.name,
            'sequence': last_sequence,
            'price_unit': price,
            'tax_id': [x.id for x in taxes],
            'discount': 0.0,
            'product_id': self.product_id.id,
            'product_uom': self.product_uom_id.id,
            'product_uom_qty': 0.0,
            'qty_delivered': self.unit_amount if not self.sheet_id or self.sheet_id.state == 'done' else 0
        }
