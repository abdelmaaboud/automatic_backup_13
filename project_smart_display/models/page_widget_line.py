# -*- coding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions SARL
# in Luxembourg 2018

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class PageWidgetLine(models.Model):
    _name = 'project.smart.display.page.widget.line'
    _order = 'sequence'

    def _get_width_values(self):
        values = []
        for value in range(1, 13):
            values.append((str(value), str(value)))
        return values
    
    page_id = fields.Many2one('project.smart.display.page')
    widget_id = fields.Many2one('project.smart.display.widget', string= "Name")
    sequence = fields.Integer(default=1)
    width = fields.Selection(selection=lambda self: self._get_width_values(), string="Width", required=True, help="6 = half width / 12 = max width")
    graph_height = fields.Integer(string="Graph height", help="50% = half height / 100% = max height. Must be superior to 25% to be big enough and Max 100%")
    name = fields.Char(related='widget_id.name')
    model = fields.Char(related='widget_id.model')
    widget_type = fields.Selection(related='widget_id.widget_type')
    field_line_ids = fields.One2many(related='widget_id.field_line_ids')
    filter_domain = fields.Text(related='widget_id.filter_domain')
    nb_results_in_list = fields.Integer(related='widget_id.nb_results_in_list')
    nb_results_to_color = fields.Integer(related='widget_id.nb_results_to_color')
    result_color = fields.Selection(related='widget_id.result_color')
    sort_by = fields.Many2one(related='widget_id.sort_by')
    sorting_order = fields.Selection(related='widget_id.sorting_order')
    summary_name = fields.Char(related='widget_id.summary_name')
    background_color = fields.Selection(related='widget_id.background_color')
    graph_type = fields.Selection(related='widget_id.graph_type')
    graph_title = fields.Char(related='widget_id.graph_title')
    group_by_field = fields.Many2one(related='widget_id.group_by_field')
    explode_biggest_part = fields.Boolean(related='widget_id.explode_biggest_part')
    x_axis_label = fields.Char(related='widget_id.x_axis_label')
    y_axis_label = fields.Char(related='widget_id.y_axis_label')
    x_axis_orientation = fields.Selection(related='widget_id.x_axis_orientation')
    horizontal_graph = fields.Boolean(related='widget_id.horizontal_graph')
    graph_color = fields.Selection(related='widget_id.graph_color')
    start_date = fields.Datetime(related='widget_id.start_date')
    period_interval = fields.Integer(related='widget_id.period_interval')
    group_by_period = fields.Selection(related='widget_id.group_by_period')
    graph_line_style = fields.Selection(related='widget_id.graph_line_style')
    operation = fields.Selection(related='widget_id.operation')
    operation_field = fields.Many2one(related='widget_id.operation_field')
    last_value_field = fields.Many2one(related='widget_id.last_value_field')
    last_value_description = fields.Char(related='widget_id.last_value_description')
    call_type = fields.Selection(related='widget_id.call_type')    
    callflow_name = fields.Selection(related='widget_id.callflow_name')
    username = fields.Selection(related='widget_id.username')

    @api.constrains('graph_height')
    def _check_height_in_range(self):
        if self.graph_height > 100 or self.graph_height < 25:
            self.graph_height = 50
            return {
                'warning': {
                    'title': _("Graph height not in range"),
                    'message': _("Graph height must be between 25% and 100%"),
                },
            }