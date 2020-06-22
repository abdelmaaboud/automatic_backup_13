from odoo import api, models, fields, _

import logging
_logger = logging.getLogger(__name__)

class Equipment(models.Model):
    _inherit = 'maintenance.equipment'

    _sql_constraints = [
        ('uniq_asset_number', 'UNIQUE(customer_id, asset_number)', _("This asset number is already attributed")),
    ]

    CRITICALITY_SELECTION = [
        ('0', 'General'),
        ('1', 'Important'),
        ('2', 'Very important'),
        ('3', 'Critical')
    ]

    criticality = fields.Selection(CRITICALITY_SELECTION, string='Criticality')
    active = fields.Boolean(string='Active', default=True)
    asset_number = fields.Char(string='Asset Number', size=64, copy=False)
    manufacturer_id = fields.Many2one('res.partner', string='Manufacturer')
    equipment_assign_to = fields.Selection(selection_add=[('customer', 'Customer')])
    customer_id = fields.Many2one('res.partner', string='Customer')
    purchase_date = fields.Date(string='Purchase Date')
    warranty_start_date = fields.Date(string='Warranty Start')
    warranty_end_date = fields.Date(string='Warranty End')
    ip = fields.Char(string='IP')
    task_ids = fields.Many2many('project.task', string="Related Tasks")
    task_count = fields.Integer(compute='_compute_task_count', string='# of Tasks')
    sale_order_line_id = fields.Many2one('sale.order.line', string='Sale Order Line')
    sale_order_id = fields.Many2one('sale.order', related='sale_order_line_id.order_id', string='Sale Order')
    worklog_ids = fields.Many2many('account.analytic.line', string="Related Worklogs")
    worklog_count = fields.Integer(compute='_compute_worklog_count', string='# of Worklogs')
    maintenance_ids = fields.Many2many('maintenance.request', 'request_equipment_rel', 'op_equipment_id', 'op_request_id', string='Maintenances')

    @api.multi
    def _compute_worklog_count(self):
        for equipment in self:
            equipment.worklog_count = self.env['account.analytic.line'].search_count([('equipment_ids', 'in', equipment.id)])

    @api.multi
    def _compute_task_count(self):
        for equipment in self:
            equipment.task_count = self.env['project.task'].search_count([('equipment_ids', 'in', equipment.id)])

    @api.multi
    @api.onchange('customer_id', 'category_id')
    def _pre_fill_asset_number(self):
        for equipment in self:
            code = ""
            # Partner code
            if equipment.equipment_assign_to == 'customer':
                if equipment.customer_id:
                    partner_code = equipment.customer_id.parent_id.ref if equipment.customer_id.parent_id else equipment.customer_id.ref
                    if partner_code:
                        code = partner_code
                    else:
                        code = equipment.customer_id.parent_id.name[0:3] if equipment.customer_id.parent_id else equipment.customer_id.name[0:3]
            # Category code
            if equipment.category_id:
                code = code + "-" + (equipment.category_id.code if equipment.category_id.code else '')
            # Asset number
            equipment_ids = equipment.customer_id.parent_id.equipment_ids if equipment.customer_id.parent_id else equipment.customer_id.equipment_ids
            same_category_asset_count = len(equipment_ids.filtered(lambda r: r.category_id == equipment.category_id))
            number = same_category_asset_count # No +1 here because the system already counts the one we are creating as member of the recordset

            if number < 10:
                if number == 0:
                    number = 1
                code = code + "-00" + str(number)
            elif number < 100:
                code = code + "-0" + str(number)
            elif number < 1000:
                code = code + "-" + str(number)

            equipment.asset_number = code
