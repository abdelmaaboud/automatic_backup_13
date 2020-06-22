# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
import logging
from odoo import models, fields, api
from odoo.tools import float_is_zero, plaintext2html


_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = ['sale.order.line']

    planned_hours = fields.Float(string='Initial Planned Hours')

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        domain = super(SaleOrderLine, self).product_id_change()

        if self.product_id.type == 'service' and 'task' in self.product_id.service_tracking:
            self.planned_hours = self.product_id.planned_hours

        return domain

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        data = super(SaleOrderLine, self).product_uom_change()

        if self.product_id.type == 'service' and 'task' in self.product_id.service_tracking:
            self.planned_hours = self.product_id.planned_hours * self.product_uom_qty

        return data

    def _timesheet_create_task_prepare_values(self):
        self.ensure_one()
        project = self._timesheet_find_project()
        # Set project Type
        project.project_type = 'installation'

        # Set project name
        project.name = (self.order_id.partner_id.ref if self.order_id.partner_id.ref else self.order_id.partner_id.name) + " - " + self.order_id.name

        # Set basic stages for the project
        project_stage_ids = self.env['project.task.type'].search([
            '|', ('name', '=ilike', 'New'),
            '|', ('name', '=ilike', 'Open'), ('name', '=ilike', 'Done')])
        project.type_ids = project_stage_ids

        planned_hours = self._convert_qty_company_hours()
        return {
            'name': '%s - %s (%s)' % (self.name, self.order_id.name, self.order_id.client_order_ref or ''),
            'planned_hours': planned_hours,
            'remaining_hours': planned_hours,
            'partner_id': self.order_id.partner_id.id,
            'description': '%s<hr />%s<hr />%s' % ((plaintext2html(self.name) if self.name else False), (self.product_id.description_sale if self.product_id.description_sale else ''), (self.product_id.description if self.product_id.description else '')),
            'project_id': project.id,
            'sale_line_id': self.id,
            'company_id': self.company_id.id,
            'email_from': self.order_id.partner_id.email,
            'user_id': False, # force non assigned task, as created as sudo()
            'stage_id': project.type_ids[0].id,
        }
