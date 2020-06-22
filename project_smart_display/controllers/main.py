# -*- coding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions SARL
# in Luxembourg 2018

from odoo import http, _
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.tools import safe_eval
from datetime import date, datetime, timedelta

import requests
import time
import logging
_logger = logging.getLogger(__name__)

class SmartDisplayPage(http.Controller):

    @http.route([
        '/smartdisplay/display/<model("project.smart.display"):display_id>',
    ], type='http', auth="public", website=True)
    def smart_display_web_page(self, page=0, display_id=None, token=None, search='', ppg=False, **post):
        if display_id.token == token:
            display_ids = http.request.env['project.smart.display'].sudo().search([('id', '=', display_id.id)])
            return http.request.render('project_smart_display.smart_display_web', {'display': display_ids})
        return http.request.render('website.404')

    @http.route([
        '/smartdisplay/getdisplay/'],
        type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def get_display(self, display_id, *kw):
        """ Ajax call to get page from id """
        if display_id:
            display = request.env['project.smart.display'].sudo().search([('id', '=', display_id)])
            callflows_dictionnary = {}
            for callflow in display.callflow_ids: # get callflows to be used by sip.js
                callflows_dictionnary.update({callflow.name: callflow.number})
                
            if not display or len(display) != 1:
                return {'display_id': -1}
            else:
                return {
                    'display_id': display.id,
                    'name': display.name,
                    'page_count': len(display.page_line_ids),
                    'delay': display.delay,
                    'show_telephony': display.show_telephony,
                    'callflows': callflows_dictionnary,
                }

    @http.route([
        '/smartdisplay/getnextpage/'],
        type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def get_next_page(self, display_id, index, *kw):
        """ Ajax call to get page for display """
        if display_id:
            display = request.env['project.smart.display'].sudo().search([('id', '=', display_id)])
            next_page = self._handle_page_index(display, index)
            if next_page == False:
                return {'page_id': -1}
            smart_dashboard_html = ''
            
            if next_page.mode == 'smart_dashboard':
                for widget in next_page.widget_line_ids:
                    eval_context = {}  # request._get_eval_context()
                    domain = []
                    
                    if widget.filter_domain:
                        domain = self._handle_domain_variables(widget, display)
                        domain = safe_eval(domain, eval_context)
                    
                    if widget.widget_type == 'graph':
                        smart_dashboard_html += '<div class="col-md-' + widget.width + '" style="height:' + str(widget.graph_height) + '%">'
                    else:
                        smart_dashboard_html += '<div class="col-md-' + widget.width + '">'
            
                    smart_dashboard_html = self._handle_widget_type(widget, smart_dashboard_html, domain) + '</div>'
                    
            return {
                'page_id': next_page.id,
                'name': next_page.name,
                'sequence': next_page.sequence,
                'mode': next_page.mode,
                'iframe_url': next_page.iframe_url,
                'smart_dashboard_html': smart_dashboard_html,
                'display_page_count': len(display.page_line_ids),
                'display_delay': display.delay,
            }

    def _handle_page_index(self, display, index):
        if not display or len(display) != 1 or len(display.page_line_ids) == 0:
            return False
        if index < 0:
            index = 0
        if index >= len(display.page_line_ids):
            index = 0
        return display.page_line_ids[index]

    def _handle_period_variables(self, domain, period, start_date, end_date):
        domain = domain.replace("'='," + period + "", "'>=','" + start_date + "'")
        index_after_field_name = domain.index("'>=','" + start_date + "'")
        index_before_field_name = domain[:index_after_field_name].rfind('(')
        new_condition = domain[index_before_field_name:][:domain[index_before_field_name:].find(')')+1].replace("'>=','" + start_date + "'", "'<=','" + end_date + "'")
        return domain[:-1] + ',' + new_condition + ']'
        
    def _handle_domain_variables(self, widget, display): # check if domain entered by user contains certain characters to convert
        domain = widget.filter_domain.replace(" ", "") # delete spaces in domain
        
        if '%_USER_ID' in domain: # replace %_USER_ID by the user id specified in the display object
            domain = domain.replace('%_USER_ID', str(display.user_id.id))
            
        start_date = datetime.now().replace(hour=0, minute=0, second=0)
        end_date = start_date.replace(hour=23, minute=59, second=59)
        if "'=',%_TODAY" in domain:
            today_start_date = str(start_date)
            today_end_date = str(end_date)
            domain = self._handle_period_variables(domain, "%_TODAY", today_start_date, today_end_date)
        if "'=',%_YESTERDAY" in domain:
            yesterday_start_date = str(start_date - timedelta(days=1))
            yesterday_end_date = str(end_date - timedelta(days=1))
            domain = self._handle_period_variables(domain, "%_YESTERDAY", yesterday_start_date, yesterday_end_date)
        if "'=',%_TOMORROW" in domain:
            tomorrow_start_date = str(start_date + timedelta(days=1))
            tomorrow_end_date = str(end_date + timedelta(days=1))
            domain = self._handle_period_variables(domain, "%_TOMORROW", tomorrow_start_date, tomorrow_end_date)
            
        return domain

    def _handle_widget_type(self, widget, smart_dashboard_html, domain):
        if widget.widget_type != 'missedCalls':
            data_ids = request.env[widget.model].sudo().search(domain, order='create_date desc')

        if widget.widget_type == 'list':
            data_ids = request.env[widget.model].sudo().search(domain, limit=widget.nb_results_in_list, order=widget.sort_by.name + ' ' + widget.sorting_order)
            smart_dashboard_html += '<h2 class="table_title">' + str(widget.name) + ' <span style="font-size: 24px;">(' + str(len(data_ids)) + ')</span></h2>'
            smart_dashboard_html = self._handle_widget_list(smart_dashboard_html, widget, data_ids)
        elif widget.widget_type == 'summary':
            smart_dashboard_html += '<div class="summary_widget" style="background-color: ' + widget.background_color + ';"><h3>' + widget.summary_name + '</h3>'
            smart_dashboard_html += '<p class="summary_value">' + str(len(data_ids)) + '</p></div>'
        elif widget.widget_type == 'graph':
            smart_dashboard_html = request.env['project.smart.display.widget']._handle_widget_graph(widget, smart_dashboard_html, data_ids)
        elif widget.widget_type == 'lastValue':
            if widget.model == 'kpi.board.value':
                data_ids = request.env[widget.model].sudo().search(domain, limit=1, order='custom_create_date desc')
            smart_dashboard_html += '<div class="summary_widget" style="background-color: ' + widget.background_color + ';"><h3>' + widget.last_value_description + '</h3>'
            smart_dashboard_html += '<p class="summary_value">' + str(data_ids[0][widget.last_value_field.name]) + '</p></div>'
        elif widget.widget_type == 'missedCalls':
            smart_dashboard_html += '<h2 class="table_title">' + str(widget.call_type) + ' calls</h2>'
            smart_dashboard_html = self._handle_widget_missed_calls(widget, smart_dashboard_html)
        return smart_dashboard_html
    
    def _handle_widget_list(self, smart_dashboard_html, widget, data_ids):
        smart_dashboard_html += '<table><tr>'
        
        for line in widget.field_line_ids:
            smart_dashboard_html += '<th>' + line.field_id.field_description + '</th>'
        smart_dashboard_html += '</tr>'
        
        if len(data_ids) == 0: # custom text if no values
            smart_dashboard_html += '<h3 style="font-style: italic; text-align: center">Table empty</h3>'
        else:
            for i, data in enumerate(data_ids):
                if widget.nb_results_to_color > 0 and i in range(0, widget.nb_results_to_color):
                    smart_dashboard_html += '<tr style="background-color: ' + widget.result_color + '">'
                else:
                    smart_dashboard_html += '<tr>'
                for line in widget.field_line_ids:
                    column_value = data[line.field_id.name] # get column's value
                    if line.field_id.ttype == 'many2one':
                        if column_value:
                            if column_value.name:
                                column_value = column_value.name
                            else:
                                column_value = column_value.id # use id if name not defined
                    elif line.field_id.ttype == 'many2many' or line.field_id.ttype == 'one2many':
                        relation_values_name = ''
                        for relation_value in column_value: # get each value from relation
                            if relation_value:
                                if relation_value.name:
                                    relation_values_name += relation_value.name + ' / '
                                else:
                                    relation_values_name += relation_value.id + ' / ' # use id if name not defined
                        column_value = relation_values_name[:-3]

                    if not column_value:
                        column_value = ""
                    smart_dashboard_html += '<td>' + str(column_value) + '</td>'
                smart_dashboard_html += '</tr>'
        smart_dashboard_html += '</table>'
        return smart_dashboard_html
    
    def _handle_widget_missed_calls(self, widget, smart_dashboard_html):
        smart_dashboard_html += '<table><tr>'

        displayed_columns = {'From', 'Date'}
        for column in displayed_columns:
            smart_dashboard_html += '<th>' + column + '</th>'
        smart_dashboard_html += '</tr>'

        API_columns = {'timestamp', 'caller_id_name'}
        for call in reversed(self._request_to_get_calls_from_API(widget).json()['data']):
            smart_dashboard_html += '<tr>'
            for column in API_columns:
                if widget.call_type == 'incoming':
                    if call['callee_id_name'] == widget.callflow_name and call['hangup_cause'] == 'NO ANSWER': # filter by callflow name and missed calls
                        if column == 'timestamp':
                            smart_dashboard_html += '<td>' + datetime.utcfromtimestamp(call[column]).strftime('%d-%m-%Y %H:%M:%S') + '</td>'
                        else:
                            smart_dashboard_html += '<td>' + call[column] + '</td>'
                else: # for INTERNAL calls
                    if call['first_name'] != None and call['last_name'] != None:
                        username = call['first_name'] + '' + call['last_name']
                        if username == widget.username and call['hangup_cause'] == 'NO ANSWER': # filter by username and missed calls
                            if column == 'timestamp':
                                smart_dashboard_html += '<td>' + datetime.utcfromtimestamp(call[column]).strftime('%d-%m-%Y %H:%M:%S') + '</td>'
                            else:
                                smart_dashboard_html += '<td>' + call[column] + '</td>'
            smart_dashboard_html += '</tr>'
        smart_dashboard_html += '</table>'
        return smart_dashboard_html
    
    def _request_to_get_calls_from_API(self, widget):
        url = "https://abakus-office.allocloud.com/v3.0/auth/user"
        data = {
            "data": {
                "username": "shaheen.kourdlassi@abakusitsolutions.eu",
                "api_key": "pD-ReHXhDGQddV3DhuYDM0-qCEBAVDuaptqYpdD5KcBnCpyANJmOzA"
            }
        }
        response = requests.put(url, json=data) # return auth_token
    
        url = "https://abakus-office.allocloud.com/v3.0/calls_history/" + widget.call_type
        timestamp = time.time()
        params = {'created_from': int(timestamp - 86400), 'created_to': int(timestamp)} # get calls from timestamp - 1 day TO timestamp
        headers = {
            'Content-Type': 'application/json',
            'X-Auth-Token': response.json()['auth_token']
        }
        return requests.get(url, params, headers=headers) # get all calls
