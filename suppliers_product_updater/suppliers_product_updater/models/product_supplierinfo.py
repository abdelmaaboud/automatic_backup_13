from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)

class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    qty_available = fields.Integer('Available Quantity')
    last_update = fields.Datetime('Last update', readonly=True)
    state = fields.Selection([('obsolete', 'Obsolete / Unavailable'), ('sellable', 'Sellable')], 'State', default='sellable')

    @api.multi
    def update_supplierinfo_with_supplier_updater(self):
        for suppinfo in self:
            self.env['supplier.updater.setting'].search([('active', '=', True), ('demo_mode', '=', False), ('supplier_id', '=', suppinfo.name.id)]).execute_updater_for_supplierinfo_ids([suppinfo])
