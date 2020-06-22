# -*- coding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions SARL
# in Luxembourg 2018

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError
from odoo.http import request
from io import BytesIO
from datetime import datetime, timedelta
from calendar import monthrange
from collections import Counter

import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
plt.style.use('ggplot')
import base64
import pandas as pd
import logging
import requests
import statistics

_logger = logging.getLogger(__name__)

class Widget(models.Model):
    _name = 'project.smart.display.widget'
    _order = 'name'

    name = fields.Char(required=True, string="Name")
    model_id = fields.Many2one('ir.model', string="Model")
    model = fields.Char()
    widget_type = fields.Selection([('list', 'List'), ('summary', 'Summary'), ('graph', 'Graph'), ('lastValue', 'Last value'), ('missedCalls', 'Missed calls')], string="Widget type", required=True)
    field_line_ids = fields.One2many('project.smart.display.widget.fields.line', 'widget_id')
    filter_domain = fields.Text(string="Domain")
    nb_results_in_list = fields.Integer(string="Number of results to display in the list", default=20)
    nb_results_to_color = fields.Integer(string="Number of results to color in the list", default=0, help="Color the first results of the list")
    result_color = fields.Selection([('#f39c12', 'Orange'), ('#74b9ff', 'Blue'), ('yellow', 'Yellow'), ('#05c46b', 'Green')], string="Result color")
    sort_by = fields.Many2one('ir.model.fields', string="Sort by")
    sorting_order = fields.Selection([('asc', 'Ascending'), ('desc', 'Descending ')], string="Sorting order")
    summary_name = fields.Char(string="Summary name", help='Describe the content of summary')
    background_color = fields.Selection([('#f39c12', 'Orange'), ('#d2dae2', 'Grey ')], string="Background color")
    graph_type = fields.Selection([('sector', 'Sector'), ('bar', 'Bar'), ('linear', 'Linear')], string="Graph type")
    graph_title = fields.Char(string="Graph title")
    group_by_field = fields.Many2one('ir.model.fields', string="Field to group by")
    explode_biggest_part = fields.Boolean(string="Explode biggest part")
    x_axis_label = fields.Char(string="Label on X axis")
    y_axis_label = fields.Char(string="Label on Y axis")
    x_axis_orientation = fields.Selection([('0', 'Horizontal'), ('90', 'Vertical'), ('45', 'Oblique')], string="Orientation for X axis labels")
    horizontal_graph = fields.Boolean(string="Horizontal graph")
    graph_color = fields.Selection([('#f39c12', 'Orange'), ('#74b9ff', 'Blue'), ('#05c46b', 'Green'), ('black', 'Black'), ('#e84118', 'Red')], string="Graph color")
    start_date = fields.Datetime(string="Start date", help="Date from which the period begins")
    period_interval = fields.Integer(string="Period interval", default=1)
    group_by_period = fields.Selection([('day', 'Day(s)'), ('week', 'Week(s)'), ('month', 'Month(s)'), ('year', 'Year(s)')], string="Period to group by", help="Data based on x axis")
    graph_line_style = fields.Selection([('solid', 'Solid'), ('dashed', 'Dashed'), ('dashdot', 'Dashdot'), ('dotted', 'Dotted')], string="Graph line style")
    operation = fields.Selection([('count', 'Count records'), ('sum', 'Sum by field'), ('average', 'Average')], string="Operation")
    operation_field = fields.Many2one('ir.model.fields', string="Field for operation")
    last_value_field = fields.Many2one('ir.model.fields', string="Field for value")
    last_value_description = fields.Char(string="Description")
    call_type = fields.Selection([('incoming', 'Incoming'), ('internal', 'Internal')], string='Missed calls type')
    callflow_name = fields.Selection(selection=lambda self: self._get_all_callflows_from_api(), string='Missed calls for', help="Select the person for whom you want to see the missed calls")
    username = fields.Selection(selection=lambda self: self._get_all_users_from_api(), string='Missed calls for', help="Select the person for whom you want to see the missed calls")
    
    @api.multi
    @api.onchange('model_id')
    def change_model(self):
        for widget in self:
            if widget.model != widget.model_id.model:
                widget.field_line_ids = False # empty field_line_ids if model change
                widget.group_by_field = False
                widget.operation_field = False
                widget.last_value_field = False
                widget.sort_by = False
            if widget.model_id:
                widget.model = widget.model_id.model

    @api.onchange('widget_type')
    def _empty_all_required_fields_if_widget_type_changes(self):
        self.field_line_ids = False
        self.nb_results_to_color = 0
        self.sort_by = False
        self.sorting_order = False
        self.summary_name = False
        self.background_color = False
        self.graph_type = False
        self.group_by_field = False
        self.x_axis_orientation = False
        self.graph_color = False
        self.start_date = False
        self.group_by_period = False
        self.graph_line_style = False
        self.last_value_field = False
        self.call_type = False
        self.callflow_name = False
        self.username = False
    
    @api.onchange('graph_type')
    def _empty_graph_required_fields_if_graph_type_changes(self):
        self.group_by_field = False
        self.x_axis_orientation = False
        self.graph_color = False
        self.start_date = False
        self.group_by_period = False
        self.period_interval = 1
        self.graph_line_style = False
        self.operation = False
        self.operation_field = False
        
    @api.onchange('nb_results_in_list')
    def _check_nb_results_in_list_superior_to_zero_and_to_nb_results_to_color(self):
        if self.nb_results_in_list < 1:
            self.nb_results_in_list = 1
            return {
                'warning': {
                    'title': _("Number of results not in range"),
                    'message': _("Number of results to display in the list must be superior to 0"),
                },
            }
        if self.nb_results_in_list < self.nb_results_to_color:
            self.nb_results_to_color = self.nb_results_in_list
    
    @api.onchange('nb_results_to_color')
    def _check_nb_results_to_color_superior_to_zero_and_inferior_to_nb_results_in_list(self):
        if self.nb_results_to_color < 0:
            self.nb_results_to_color = 0
            return {
                'warning': {
                    'title': _("Number of results to color not in range"),
                    'message': _("Number of results to color in the list must be greater than or equal to 0"),
                },
            }
        elif self.nb_results_to_color > self.nb_results_in_list:
            self.nb_results_to_color = self.nb_results_in_list
            return {
                'warning': {
                    'title': _("Number of results to color not in range"),
                    'message': _("Number of results to color in the list must be less than or equal to number of results to display in the list"),
                },
            }

    @api.onchange('period_interval')
    def _check_period_interval_superior_to_zero(self):
        if self.period_interval < 1:
            self.period_interval = 1
            return {
                'warning': {
                    'title': _("Period interval not in range"),
                    'message': _("Period interval must be superior to 0"),
                },
            }
    
    @api.constrains('field_line_ids')
    def _check_nb_fields_superior_to_zero(self):
        if self.widget_type == 'list' and len(self.field_line_ids) < 1:
            raise exceptions.ValidationError("Please select at least one column to display")
    
    def _generate_API_token(self):
        url = "https://abakus-office.allocloud.com/v3.0/auth/user"
        data = {
            "data": {
                "username": self.env['ir.config_parameter'].sudo().get_param('allocloud_api_username'),
                "api_key": self.env['ir.config_parameter'].sudo().get_param('allocloud_api_key'),
            }
        }
        return requests.put(url, json=data) # return auth_token
        
    def _request_to_API(self, url):
        headers = {
            'Content-Type': 'application/json',
            'X-Auth-Token': self._generate_API_token().json()['auth_token']
        }
        return requests.get(url, headers=headers)
        
    def _get_all_callflows_from_api(self):
        url = "https://abakus-office.allocloud.com/v3.0/callflows"
        response = self._request_to_API(url)
        callflows = []
        if 'data' in response.json():
            for callflow in response.json()['data']:
                if callflow['featurecode'] == False:
                    callflows.append((callflow['name'], callflow['name']))
        return callflows
        
    def _get_all_users_from_api(self):
        url = "https://abakus-office.allocloud.com/v3.0/users"
        response = self._request_to_API(url)
        users = []
        if 'data' in response.json():
            for user in response.json()['data']:
                users.append((user['first_name'] + user['last_name'], user['first_name'] + ' ' + user['last_name']))
        return users
        
    """
    Next part concerns graph generation and a verification to handle a possible exception
    """
    """
        TODO: Make this work. Goal : check the coherence of the widget on creation and handle the error, before facing an error on the front-end
    @api.constrains('group_by_field')
    def _check_graph_generated_without_error(self):
        try:
            data_ids = self.env[self.model].sudo().search(self.filter_domain, order='create_date desc')
            self._handle_widget_graph(self, 'for exception', data_ids)
        except Exception as e:
            raise exceptions.ValidationError(e) # display exception if a graph generate one
    """
            
    def _handle_widget_graph(self, widget, smart_dashboard_html, data_ids):
        if widget.graph_type == 'sector':
            smart_dashboard_html = self._handle_graph_sector(smart_dashboard_html, widget, data_ids)
        elif widget.graph_type == 'bar':
            smart_dashboard_html = self._handle_graph_bar(smart_dashboard_html, widget, data_ids)
        elif widget.graph_type == 'linear':
            smart_dashboard_html = self._handle_graph_linear(smart_dashboard_html, widget, data_ids)
        return smart_dashboard_html
    
    def _handle_graph_sector(self, smart_dashboard_html, widget, data_ids):
        result = self._generate_labels_and_values_for_graph_sector_and_bar(widget, data_ids)
        labels = result[0]
        values = result[1]
        explode = [0] * len(values)
        
        if widget.explode_biggest_part:
            max_value_pos = values.index(max(values))
            explode[max_value_pos] = 0.2 # default value
        
        fig, ax = plt.subplots()
        if widget.graph_title:
            ax.set_title(widget.graph_title, bbox=dict(facecolor='none', edgecolor='black', boxstyle='round,pad=0.5'))
        ax.pie(values, labels=labels, explode=explode, autopct=lambda p: '{:.2f}%  ({:,.0f})'.format(p,p * sum(values)/100))
        tmpfile = BytesIO()
        fig.savefig(tmpfile, format='png')
        decoded = base64.b64encode(tmpfile.getvalue()).decode('utf8')

        smart_dashboard_html += "<img src='data:image/png;base64,{}' class='graph_img' />".format(decoded)
        return smart_dashboard_html
    
    def _handle_graph_bar(self, smart_dashboard_html, widget, data_ids):
        result = self._generate_labels_and_values_for_graph_sector_and_bar(widget, data_ids)
        labels = result[0]
        values = result[1]
        
        fig, ax = plt.subplots()
        if widget.graph_title:
            ax.set_title(widget.graph_title)
        if widget.x_axis_label:
            ax.set_xlabel(widget.x_axis_label)
        if widget.y_axis_label:
            ax.set_ylabel(widget.y_axis_label)
        nb_elements_axis_x = range(len(labels))
        if widget.horizontal_graph:
            ax.barh(nb_elements_axis_x, values, align='center', color=widget.graph_color, edgecolor='black')
            ax.set_yticks(nb_elements_axis_x)
            ax.set_yticklabels(labels, rotation=widget.x_axis_orientation)
            for i, v in enumerate(values):
                ax.text(v + 0.1, i, str(v), fontweight='bold')
        else:
            ax.bar(nb_elements_axis_x, values, align='center', color=widget.graph_color, edgecolor='black')
            ax.set_xticks(nb_elements_axis_x)
            ax.set_xticklabels(labels, rotation=widget.x_axis_orientation)
            for i, v in enumerate(values):
                ax.text(i, v, str(v), fontweight='bold', ha='center', va='bottom')
        tmpfile = BytesIO()
        fig.savefig(tmpfile, format='png')
        decoded = base64.b64encode(tmpfile.getvalue()).decode('utf8')

        smart_dashboard_html += "<img src='data:image/png;base64,{}' class='graph_img' />".format(decoded)
        return smart_dashboard_html

    def _generate_labels_and_values_for_graph_sector_and_bar(self, widget, data_ids):
        labels = []
        values = []
        nb_occurence_for_label_other = 0
        field = widget.group_by_field
        field_values = data_ids.mapped(field.name)
        dict_values_counter = Counter(field_values)

        if len(dict_values_counter) > 0:
            for k,v in dict_values_counter.items():
                if field.ttype == 'many2one':
                    if k.name in [False, 'none', None]:
                        nb_occurence_for_label_other += v
                    else:
                        labels.append(k.name)
                        values.append(v)
                else:
                    if k in [False, 'none', None]:
                        nb_occurence_for_label_other += v
                    else:
                        labels.append(k)
                        values.append(v)

            if nb_occurence_for_label_other > 0:
                labels.append('Other') # create "Other" label for field value in [False, 'none']
                values.append(nb_occurence_for_label_other)
        else:
            raise ValueError('No data for specified field. Please group by an other field.')
            
        return [labels, values]
        
    def _handle_graph_linear(self, smart_dashboard_html, widget, data_ids):
        labels = []
        values = []
        result = []
        date = datetime.strptime(widget.start_date, '%Y-%m-%d %H:%M:%S')
        
        if widget.group_by_period == 'day':
            result = self._handle_graph_linear_grouped_by_day(widget, date, labels, values)
        elif widget.group_by_period == 'week':
            result = self._handle_graph_linear_grouped_by_week(widget, date, labels, values)
        elif widget.group_by_period == 'month':
            result = self._handle_graph_linear_grouped_by_month(widget, date, labels, values)
        elif widget.group_by_period == 'year':
            result = self._handle_graph_linear_grouped_by_year(widget, date, labels, values)
        
        labels = result[0]
        values = result[1]
        if smart_dashboard_html == 'for exception': # avoids an exception to catch a group by field exception if it exists
            fig, ax = plt.subplots()
        else:
            fig, ax = plt.subplots()
        if widget.graph_title:
            ax.set_title(widget.graph_title)
        if widget.x_axis_label:
            ax.set_xlabel(widget.x_axis_label)
        if widget.y_axis_label:
            ax.set_ylabel(widget.y_axis_label)
        ax.plot(labels, values, color=widget.graph_color, linestyle=widget.graph_line_style, linewidth=2.0)
        ax.set_xticklabels(labels, rotation=widget.x_axis_orientation)
        
        tmpfile = BytesIO()
        fig.savefig(tmpfile, format='png')
        decoded = base64.b64encode(tmpfile.getvalue()).decode('utf8')

        smart_dashboard_html += "<img src='data:image/png;base64,{}' class='graph_img' />".format(decoded)
        return smart_dashboard_html
    
    def _handle_graph_linear_grouped_by_day(self, widget, date, labels, values):
        for i in range(widget.period_interval):
            if i != 0: # allows to include start_date
                date += timedelta(days=1)
            start_day_date = datetime.strftime(date.replace(hour=0, minute=0, second=0), '%Y-%m-%d %H:%M:%S')
            end_day_date = datetime.strftime(date.replace(hour=23, minute=59, second=59), '%Y-%m-%d %H:%M:%S')
            value = self._handle_graph_linear_operation(widget, start_day_date, end_day_date)
            labels.append(date.strftime('%d/%m/%Y')) # change date format to display it on X axis
            values.append(value)
        return [labels, values]
    
    def _handle_graph_linear_grouped_by_week(self, widget, date, labels, values):
        for i in range(widget.period_interval):
            monday_date = datetime.strftime(date.replace(hour=0, minute=0, second=0) - timedelta(days=date.weekday()), '%Y-%m-%d %H:%M:%S')
            friday_date = datetime.strftime(date.replace(hour=23, minute=59, second=59) + timedelta(days=4), '%Y-%m-%d %H:%M:%S')
            value = self._handle_graph_linear_operation(widget, monday_date, friday_date)
            if i == 0:
                labels.append('This week')
            else:
                labels.append('Week %s' % i)
            values.append(value)
            friday_datetime = datetime.strptime(friday_date, '%Y-%m-%d %H:%M:%S')
            date = friday_datetime + timedelta(days=(0 - friday_datetime.weekday() + 7) % 7) # get next monday date
        return [labels, values]
        
    def _handle_graph_linear_grouped_by_month(self, widget, date, labels, values):
        for i in range(widget.period_interval):
            days_in_month = monthrange(date.year, date.month)[1]
            month_start_date = datetime.strftime(date.replace(day=1, hour=0, minute=0, second=0), '%Y-%m-%d %H:%M:%S')
            month_end_date = datetime.strftime(date.replace(day=days_in_month, hour=23, minute=59, second=59), '%Y-%m-%d %H:%M:%S')
            value = self._handle_graph_linear_operation(widget, month_start_date, month_end_date)
            labels.append(datetime.strftime(date, '%Y-%m'))
            values.append(value)
            date += timedelta(days_in_month) # get same date for next month
        return [labels, values]
        
    def _handle_graph_linear_grouped_by_year(self, widget, date, labels, values):
        for i in range(widget.period_interval):
            year_start_date = datetime.strftime(date.replace(day=1, month=1, hour=0, minute=0, second=0), '%Y-%m-%d %H:%M:%S')
            year_end_date = datetime.strftime(date.replace(day=31, month=12, hour=23, minute=59, second=59), '%Y-%m-%d %H:%M:%S')
            value = self._handle_graph_linear_operation(widget, year_start_date, year_end_date)
            labels.append(datetime.strftime(date, '%Y'))
            values.append(value)
            date = date.replace(year=date.year + 1) # get same date for next year
        return [labels, values]
    
    def _handle_graph_linear_operation(self, widget, start_date, end_date):
        values = request.env[widget.model].sudo().search([('create_date', '>=', start_date), ('create_date', '<=', end_date)]).mapped(widget.operation_field.name) #TODO : use the domain specified in the widget here
        if widget.operation == 'count':
            return len(values)
        elif widget.operation == 'sum':
            return sum(values)
        elif widget.operation == 'average':
            if len(values) > 0:
                return "{:.2f}".format(statistics.mean(values))
            else:
                return 0
