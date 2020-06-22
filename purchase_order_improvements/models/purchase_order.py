import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit="purchase.order"
    
    @api.model
    def create(self, vals):
        if 'order_line' in vals:
            for line in vals['order_line']:
                product_id = self.env['product.product'].browse(line[2]['product_id'])
                if not line[2]['account_analytic_id'] and not product_id.expense_analytic_account_id and (not product_id.categ_id or not product_id.categ_id.expense_analytic_account_id):
                    raise UserError(_("Atleast one order line doesn't have an analytic account selected. Please select an analytic account."))
        return super(PurchaseOrder, self).create(vals)

class PurchaseOrderLine(models.Model):
    _inherit="purchase.order.line"

    @api.multi
    def _compute_tax_id(self):
        for line in self:
            fpos = line.order_id.fiscal_position_id or line.order_id.partner_id.property_account_position_id
            # If company_id is set, always filter taxes by the company
            taxes = line.product_id.supplier_taxes_id.filtered(
                lambda r: not line.company_id or r.company_id == line.company_id)
            if not taxes and line.product_id.categ_id:
                taxes = line.product_id.categ_id.supplier_taxes_id.filtered(lambda r: not line.company_id or r.company_id == line.company_id)
            line.taxes_id = fpos.map_tax(taxes, line.product_id, line.order_id.partner_id) if fpos else taxes

    @api.multi
    def write(self, vals):
        res =  super(PurchaseOrderLine, self).write(vals)
        for _self in self:
            if not _self.account_analytic_id and not _self.product_id.expense_analytic_account_id and (not _self.product_id.categ_id or not _self.product_id.categ_id.expense_analytic_account_id):
                raise UserError(_("Atleast one order line doesn't have an analytic account selected. Please select an analytic account."))
        return res
