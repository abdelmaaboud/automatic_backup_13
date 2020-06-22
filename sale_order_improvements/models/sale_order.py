# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
from odoo import models, fields


class SaleOrderImprovements(models.Model):
    _inherit = 'sale.order'

    partner_invoice_id = fields.Many2one('res.partner', readonly=False)
    attachments_ids = fields.Many2many('ir.attachment', string="Attachments")
    header_text = fields.Html(string="Optional header text")
    note = fields.Html("Terms and conditions")
    internal_order_ref = fields.Char("Internal Reference")
