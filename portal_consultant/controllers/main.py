# -*- coding: utf-8 -*-
import logging
import base64
import re
from datetime import datetime, time
from odoo import http, _, fields
from odoo.http import request
from odoo.exceptions import UserError, ValidationError, AccessError
from odoo.addons.portal.controllers.portal import CustomerPortal

_logger = logging.getLogger(__name__)


class PortalConsultant(CustomerPortal):

    def conv_time_float(self, value):
        vals = value.split(':')

        try:
            hours = float(vals[0])
        except ValueError:
            values = vals[0].split(',')
            fusion = str(values[0]) + "." + str(values[1])
            value = float(fusion)
            hours, minutes = divmod(value * 60, 60)
            minutes = minutes / 60.0
            return hours + minutes
        try:
            minutes = float(vals[1]) / 60.0
        except IndexError:
            return hours

        return hours + minutes

    def get_or_create_timesheet(self, sheet_id, user, project, task, date_str):
        if not sheet_id or not user or not project or not task or not date_str:
            raise ValidationError(_("There is a problem with account.analytic.line values!"))
        timesheet_id = sheet_id.timesheet_ids.filtered(
            lambda t: t.date == date_str and t.project_id.id == project and t.task_id.id == task)
        if not timesheet_id:
            timesheet_id = self.create_timesheet_id(sheet_id, user, project, task, date_str)
        elif timesheet_id and len(timesheet_id) > 1:
            timesheet_id = timesheet_id[0]
        return timesheet_id

    def create_timesheet_id(self, sheet_id, user, project, task, date_str):
        if not user.resource_calendar_id or not user.resource_calendar_id.attendance_ids:
            raise ValidationError(_("You must specify a working schedule for the user!"))
        attendance_ids = user.resource_calendar_id.attendance_ids
        date = fields.Date.from_string(date_str)
        current_weekday = date.weekday()
        return request.env['account.analytic.line'].sudo().create({
            'project_id': project,
            'task_id': task,
            'amount': 0.0,
            'date': date_str,
            'date_begin': fields.Datetime.to_string(datetime.combine(date, self._get_time_from_day(current_weekday, attendance_ids))),
            'employee_id': user.employee_ids[0].id,
            'unit_amount': 0.0,
            'sheet_id': sheet_id.id,
        })

    def _prepare_values(self, user, default_project, default_task, info):
        return {
            'info': info,
            'page_name': 'my_timesheets_form',
            'user': user,
            'res_cal': user.resource_calendar_id,
            'WEEKDAY_TO_NAME': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
            'project_projects': request.env['project.project'].sudo().search(
                [("portal_selectable", '=', True), ("id", '!=', default_project.id)]),
            'project_1': default_project,
            'task_1': default_task,
        }

    def _get_time_from_day(self, current_weekday, attendance_ids):
        attendance_id = attendance_ids.filtered(lambda a: a.dayofweek == current_weekday).sorted('hour_from')
        if not attendance_id:
            return time(8, 30)
        if len(attendance_id) > 1:
            attendance_id = attendance_id[0]
        hour_from = attendance_id.hour_from
        return time(int(hour_from), hour_from % 1 * 60)

    def _compute_name(self, date):
        date_conv = datetime.strptime(date, "%Y-%m-%d")
        return '%s %s' % (datetime.strftime(date_conv, "%B"), datetime.strftime(date_conv, "%Y"))

    def is_overlapped(self, date_start, date_end, timesheet=False):
        dates = datetime.strptime(date_start, "%Y-%m-%d")
        datee = datetime.strptime(date_end, "%Y-%m-%d")
        user_id, employee_id = self.get_user_and_employee()
        domain = [("date_start", '<=', datee), ("date_end", '>=', dates), ("employee_id", '=', employee_id.id)]
        if timesheet:
            domain += [("id", '!=', timesheet.id)]
        return request.env['hr_timesheet.sheet'].sudo().search(domain).exists()

    def is_date_end_before_date_start(self, date_start, date_end):
        dates = datetime.strptime(date_start, "%Y-%m-%d")
        datee = datetime.strptime(date_end, "%Y-%m-%d")
        return dates > datee

    def is_correct_time_format(self, hours):
        x = re.findall("(\d+[,:.]{1}\d+)|(\d+)", hours)
        return hours in [el[0] if el[0] else el[1] for el in x]

    def download_attachment(self, attachment):
        if not attachment:
            raise ValidationError(_("There is no attachment for this ID!"))

        file = request.env['ir.attachment'].sudo().search([("id", '=', attachment)])

        content = file.datas
        image_base64 = 0
        if content:
            image_base64 = base64.b64decode(content)
        if not file.mimetype:
            raise ValidationError(_("There is no mimetype for the attachment!"))
        headers = [('Content-Type', file.mimetype)]
        response = request.make_response(image_base64, headers)
        return response

    def get_user_and_employee(self):
        user = request.env.user
        employee_id = request.env['hr.employee'].sudo().search([('user_id', '=', user.id), ('company_id', '=', user.company_id.id)], limit=1)
        if not employee_id:
            raise ValidationError(_("Your user must be link to one employee for the current company!"))
        return user, employee_id
    
    @http.route(['/my/get_project_tasks/<int:project_id>'], type='json', auth="user", website=True)
    def get_project_tasks(self, project_id, **kw):
        user, employee_id = self.get_user_and_employee()
        project = request.env['project.project'].sudo().search([('id', '=', project_id), ('portal_selectable', '=', True)])
        tasks_json = []
        tasks = request.env['project.task'].sudo().search([('project_id', '=', project.id)])
        for task in tasks:
            tasks_json.append({'id': task.id, 'name': task.name})
        return {
            'result': tasks_json
        }

    @http.route(['/my/check_date'], type='json', auth="user", website=True)
    def check_date(self, **kw):
        user, employee_id = self.get_user_and_employee()

        start_date = datetime.strptime(kw['start_date'], "%Y-%m-%d").date()
        end_date = datetime.strptime(kw['end_date'], "%Y-%m-%d").date()

        datetime_from = request.env['hr.holidays'].sudo().get_datetime_from_date_and_moment(start_date, kw['start_moment'], employee_id)
        datetime_to = request.env['hr.holidays'].sudo().get_datetime_from_date_and_moment(end_date, kw['end_moment'], employee_id)
        number_of_days = request.env['hr.holidays'].sudo()._get_number_of_days(str(datetime_from), str(datetime_to), employee_id.id)
        return {
            'result': {
                'datetime_from': datetime_from,
                'datetime_to': datetime_to,
                'number_of_days': number_of_days,
            }
        }

    @http.route(['/my', '/my/home'], type='http', auth="user", website=True)
    def home(self, **kw):
        user = request.env.user
        employee_id = request.env['hr.employee'].sudo().search([('user_id', '=', user.id), ('company_id', '=', user.company_id.id)], limit=1)
        if not employee_id:
            return super(PortalConsultant, self).home(**kw)
        values = self._prepare_portal_layout_values()
        user, employee_id = self.get_user_and_employee()

        values.update({
            'expense_count': request.env['hr.expense'].sudo().search_count([("employee_id", '=', employee_id.id)]),
            'leave_count': request.env['hr.holidays'].sudo().search_count([("employee_id", '=', employee_id.id)]),
            'timesheet_count': request.env['hr_timesheet.sheet'].sudo().search_count([("employee_id", '=', employee_id.id)]),
            'help_text': employee_id.company_id.portal_help_home if employee_id.company_id.portal_help_home else '',
            'user': user,
            'portal_consultant': True,
        })

        return request.render("portal.portal_my_home", values)

    @http.route(['/my/expenses'], type='http', auth="user", website=True)
    def _prepare_portal_layout_expense_values(self):
        user, employee_id = self.get_user_and_employee()

        values = {
            'expenses': request.env['hr.expense'].sudo().search([("employee_id", '=', employee_id.id)]),
            'page_name': 'my_expenses',
            'help_text': employee_id.company_id.portal_help_expense_list_view if employee_id.company_id.portal_help_expense_list_view else '',
            }
        return request.render("portal_consultant.portal_my_expenses", values)

    @http.route(['/my/expenses/form/<int:expense>'], type='http', auth="user", website=True)
    def expense_form(self, expense):
        user, employee_id = self.get_user_and_employee()

        products = request.env['product.product'].sudo().search([("can_be_expensed", '=', 'True')])
        if not products:
            raise ValidationError(_("There is a no the products that can be expensed for the company"))
        currency_id = request.env.user.company_id.currency_id.id
        if not currency_id:
            raise ValidationError(_("There is a problem with the currency of the company"))
        values = {
            'page_name': 'my_expenses_form',
            'expense_id': False,
            'products': products,
            'attachments': False,
            'currency_id': currency_id,
            'help_text': employee_id.company_id.portal_help_expense_form_view if employee_id.company_id.portal_help_expense_form_view else '',
        }

        if expense != -1:
            expense_id = request.env['hr.expense'].sudo().search([("id", '=', expense), ('employee_id', '=', employee_id.id)])
            attachments = request.env['ir.attachment'].sudo().search([("res_id", '=', expense_id.id), ("res_model", '=', 'hr.expense')])

            if expense_id:
                values.update({'expense_id': expense_id})
            if attachments:
                values.update({'attachments': attachments})
        return request.render("portal_consultant.portal_form_expense", values)

    @http.route(['/my/expenses/edit'], type='http', auth="user", method=['POST'], website=True)
    def expense_new(self, **post):
        user, employee_id = self.get_user_and_employee()

        if 'expense_date' not in post \
                or 'expense_name' not in post \
                or 'expense_description' not in post \
                or 'product_name' not in post \
                or 'expense_unit_price' not in post:
            return request.render('website.404')
        if 'expense_id' in post:
            product_id = request.env['product.product'].sudo().browse(int(post['product_name']))
            if product_id:
                expense_id = request.env['hr.expense'].sudo().search([("id", '=', post['expense_id'])])
                if not expense_id:
                    raise ValidationError(_("This expense does not exist!"))

                currency_id = request.env.user.company_id.currency_id.id
                if not currency_id:
                    raise ValidationError(_("There is a problem with the currency of the company"))
                expense_id.write({
                    'date': post['expense_date'],
                    'name': post['expense_name'],
                    'description': post['expense_description'],
                    'employee_id': employee_id.id,
                    'product_id': post['product_name'],
                    'product_uom_id': product_id.uom_id.id,
                    'quantity': 1,
                    'unit_amount': post['expense_unit_price'],
                    'currency_id': employee_id.company_id.currency_id.id,
                    'company_id': employee_id.company_id.id,
                })
                if 'expense_file' in post and post.get('expense_file'):
                    attached_files = request.httprequest.files.getlist('expense_file')
                    for attachment in attached_files:
                        attached_file = attachment.read()
                        request.env['ir.attachment'].sudo().create({
                            'name': attachment.filename,
                            'res_model': 'hr.expense',
                            'res_id': expense_id.id,
                            'type': 'binary',
                            'datas_fname': attachment.filename,
                            'datas': base64.b64encode(attached_file),
                        })
                return request.redirect('/my/expenses/form/' + str(expense_id.id))
            else:
                return request.redirect('/my/expenses')
        else:
            product_id = request.env['product.product'].sudo().browse(int(post['product_name']))
            if product_id:
                new_expense_id = request.env['hr.expense'].sudo().create({
                    'date': post['expense_date'],
                    'name': post['expense_name'],
                    'description': post['expense_description'],
                    'employee_id': employee_id.id,
                    'product_id': post['product_name'],
                    'product_uom_id': product_id.uom_id.id,
                    'quantity': 1,
                    'unit_amount': post['expense_unit_price'],
                    'currency_id': employee_id.company_id.currency_id.id,
                    'company_id': employee_id.company_id.id,
                })
                if 'expense_file' in post and post.get('expense_file'):
                    attached_files = request.httprequest.files.getlist('expense_file')
                    for attachment in attached_files:
                        attached_file = attachment.read()
                        request.env['ir.attachment'].sudo().create({
                            'name': attachment.filename,
                            'res_model': 'hr.expense',
                            'res_id': new_expense_id.id,
                            'type': 'binary',
                            'datas_fname': attachment.filename,
                            'datas': base64.b64encode(attached_file),
                        })
                return request.redirect('/my/expenses')
            else:
                return request.redirect('/my/expenses')

    @http.route(['/my/expenses/delete/<int:expense>'], type='http', auth="user", website=True)
    def expense_delete(self, expense):
        user, employee_id = self.get_user_and_employee()

        if expense:
            expense_id = request.env['hr.expense'].sudo().search([("id", '=', expense), ('employee_id', '=', employee_id.id)])
            if not expense_id:
                raise ValidationError(_("There is no expense with this ID!"))
            expense_id.unlink()
            attachment_linked = request.env['ir.attachment'].sudo().search([("res_id", '=', expense), ("res_model", '=', 'hr.expense')])
            if attachment_linked:
                attachment_linked.unlink()
        return request.redirect('/my/expenses')

    @http.route(['/my/expenses/delete/attachment/<int:attachment>'], type='http', auth="user", website=True)
    def expense_delete_attachment(self, attachment):
        user, employee_id = self.get_user_and_employee()
        if not attachment:
            raise ValidationError(_("There is no ID for the attachment!"))
        attachment = request.env['ir.attachment'].sudo().search([("id", '=', attachment),("res_model", '=', 'hr.expense')])
        expense_id = attachment.res_id
        expense = request.env['hr.expense'].sudo().search([('id', '=', expense_id), ('employee_id', '=', employee_id.id)])
        if not expense:
            raise ValidationError(_("Attachment doesn't exist or it's not yours."))
        attachment.sudo().unlink()
        if expense_id:
            return request.redirect('/my/expenses/form/' + str(expense_id))
        else:
            return request.redirect('/my/expenses')

    @http.route(['/my/expenses/download/attachment/<int:attachment>'], type='http', auth="user", website=True)
    def expense_dl_attachment(self, attachment):
        user, employee_id = self.get_user_and_employee()
        res_id = request.env['ir.attachment'].sudo().search([("id", '=', attachment), ("res_model", '=', 'hr.expense')], limit=1).res_id
        attachment_employee = request.env['hr.expense'].sudo().browse(res_id).employee_id

        if employee_id.id != attachment_employee.id:
            raise ValidationError(_("This attachment is not available for this employee!"))
        return self.download_attachment(attachment)

    @http.route(['/my/expenses/submit/<int:expense>'], type='http', auth="user", website=True)
    def expense_submit(self, expense):
        user, employee_id = self.get_user_and_employee()

        expense_id = request.env['hr.expense'].sudo().search([('id', '=', expense), ('employee_id', '=', employee_id.id)]) # TODO check that this expense belongs to the current employee DONE
        if not expense_id:
            raise ValidationError(_("This expense does not exist!"))
        journal_id = request.env['account.journal'].sudo().search([('company_id', '=', employee_id.company_id.id), ('code', 'ilike', 'exp'), ('type', '=', 'purchase')])
        if not journal_id:
            raise ValidationError(_("There is no accounting journal for the company to encode the expense sheet on. Please contact your admin with this error."))
        expense_sheet = request.env['hr.expense.sheet'].sudo().create({
            'name': expense_id.name,
            'employee_id': employee_id.id,
            'state': 'submit',
            'expense_line_ids': expense_id,
            'company_id': employee_id.company_id.id,
            'journal_id': journal_id.id,
        })
        expense_id.sudo().write({'sheet_id': expense_sheet.id})
        return request.redirect('/my/expenses')

    @http.route(['/my/leaves'], type='http', auth="user", website=True)
    def _prepare_portal_layout_leaves_values(self):
        user, employee_id = self.get_user_and_employee()

        values = {
            'leaves': request.env['hr.holidays'].sudo().search([("employee_id", '=', employee_id.id)]),
            'page_name': 'my_leaves',
            'help_text': employee_id.company_id.portal_help_leave_list_view if employee_id.company_id.portal_help_leave_list_view else '',
        }
        return request.render("portal_consultant.portal_my_leaves", values)

    @http.route(['/my/leaves/form/<int:leave>'], type='http', auth="user", website=True)
    def leave_form(self, leave, m=None):
        user, employee_id = self.get_user_and_employee()

        types = request.env['hr.holidays.status'].sudo().search(['|', ('company_id', '=', employee_id.company_id.id), ('company_id', '=', False)])
        for leave_type in types:
            result = leave_type.get_days(employee_id.id)
            for attr in result:
                leave_type.remaining_leaves = result[attr].get('remaining_leaves')

        if not types:
            raise ValidationError(_("There is a problem with the leaves types!"))
        values = {
            'page_name': 'my_leaves_form',
            'leave_id': False,
            'leave_types': types,
            'help_text': employee_id.company_id.portal_help_leave_form_view if employee_id.company_id.portal_help_leave_form_view else '',
        }
        if leave != -1:
            leave_id = request.env['hr.holidays'].sudo().search([("id", '=', leave), ("employee_id", '=', employee_id.id)])
            if not leave_id:
                raise ValidationError(_("There is no leave with this ID!"))
            values.update({'leave_id': leave_id})
            attachments = request.env['ir.attachment'].sudo().search([("res_id", '=', leave_id.id), ("res_model", '=', 'hr.holidays')])
            if attachments:
                values.update({'attachments': attachments})
        if m:
            values.update({'info': m})
        return request.render("portal_consultant.portal_form_leave", values)

    @http.route(['/my/leaves/edit'], type='http', auth="user", method=['POST'], website=True)
    def leave_new(self, **post):
        user, employee_id = self.get_user_and_employee()
        if 'leave_holiday_status' not in post \
                or 'leave_name' not in post \
                or 'leave_start_date' not in post \
                or 'leave_end_date' not in post \
                or 'leave_number_of_days' not in post:
            return request.render('website.404')
        if 'leave_id' in post:
            try:
                with request.env.cr.savepoint():
                    holiday = request.env['hr.holidays'].sudo().search([("id", '=', post['leave_id']), ("employee_id", '=', employee_id.id)])
                    if not holiday:
                        raise ValidationError(_("This leave does not exist!"))
                    holiday.sudo().write({
                        'holiday_status_id': post['leave_holiday_status'],
                        'holiday_type': 'employee',
                        'type': 'remove',
                        'name': post['leave_name'],
                        'date_from': post['leave_start_date'],
                        'date_to': post['leave_end_date'],
                        'day_time_from': post['leave_start_moment'],
                        'day_time_to': post['leave_end_moment'],
                        'number_of_days': - float(post['leave_number_of_days']),
                        'number_of_days_temp': post['leave_number_of_days'],
                        'employee_id': user.employee_ids.id,
                    })
                    if 'leave_file' in post and post.get('leave_file'):
                        attachments = request.env['ir.attachment']
                        name = post.get('leave_file').filename
                        file = post.get('leave_file')
                        attachment = file.read()
                        attachment_id = attachments.sudo().create({
                            'name': name,
                            'datas_fname': name,
                            'type': 'binary',
                            'res_model': 'hr.holidays',
                            'res_id': holiday.id,
                            'datas': base64.b64encode(attachment),
                        })
                    return request.redirect('/my/leaves/form/' + str(holiday.id))
            except Exception as e:
                return request.redirect('/my/leaves/form/' + post['leave_id'] + "?m=" + str(e))
        else:
            try:
                with request.env.cr.savepoint():
                    date_from = request.env['hr.holidays'].sudo().get_datetime_from_date_and_moment(
                        datetime.strptime(post['leave_start_date'], "%Y-%m-%d").date(), post['leave_start_moment'],
                        employee_id)
                    date_to = request.env['hr.holidays'].sudo().get_datetime_from_date_and_moment(
                        datetime.strptime(post['leave_end_date'], "%Y-%m-%d").date(), post['leave_end_moment'],
                        employee_id)
                    new_leave = request.env['hr.holidays'].sudo().create({
                        'holiday_status_id': post['leave_holiday_status'],
                        'holiday_type': 'employee',
                        'type': 'remove',
                        'name': post['leave_name'],
                        'date_from': date_from,
                        'date_to': date_to,
                        'date_day_from': post['leave_start_date'],
                        'date_day_to': post['leave_end_date'],
                        'day_time_from': post['leave_start_moment'],
                        'day_time_to': post['leave_end_moment'],
                        'number_of_days': - float(post['leave_number_of_days']),
                        'number_of_days_temp': post['leave_number_of_days'],
                        'employee_id': user.employee_ids.id,
                    })
                    if 'leave_file' in post and post.get('leave_file'):
                        attachments = request.env['ir.attachment']
                        name = post.get('leave_file').filename
                        file = post.get('leave_file')
                        attachment = file.read()
                        attachment_id = attachments.sudo().create({
                            'name': name,
                            'datas_fname': name,
                            'type': 'binary',
                            'res_model': 'hr.holidays',
                            'res_id': new_leave.id,
                            'datas': base64.b64encode(attachment),
                        })
                    return request.redirect('/my/leaves')
            except Exception as e:
                return request.redirect('/my/leaves/form/-1' + "?m=" + str(e))

    @http.route(['/my/leaves/delete/<int:leave>'], type='http', auth="user", website=True)
    def leave_delete(self, leave):
        user, employee_id = self.get_user_and_employee()
        if leave:
            request.env['hr.holidays'].sudo().search([("id", '=', leave), ("employee_id", '=', employee_id.id)]).unlink()
        attachment_linked = request.env['ir.attachment'].sudo().search([("res_id", '=', leave), ("res_model", '=', 'hr.holidays')])
        if attachment_linked:
            attachment_linked.unlink()
        return request.redirect('/my/leaves')

    @http.route(['/my/leaves/delete/attachment/<int:attachment>'], type='http', auth="user", website=True)
    def leave_delete_attachment(self, attachment):
        user, employee_id = self.get_user_and_employee()
        if not attachment:
            raise ValidationError(_("There is no attachment for this leave!"))
        attachment = request.env['ir.attachment'].sudo().search([("id", '=', attachment), ("res_model", '=', 'hr.holidays')])
        leave_id = attachment.res_id
        leave = request.env['hr.holidays'].sudo().search([('id', '=', leave_id), ('employee_id', '=', employee_id.id)])
        if not leave:
            raise ValidationError(_("This attachment doesn't exist or it's not yours."))
        attachment.sudo().unlink()
        if leave_id:
            return request.redirect('/my/leaves/form/' + str(leave_id))
        else:
            return request.redirect('/my/leaves')

    @http.route(['/my/leaves/download/attachment/<int:attachment>'], type='http', auth="user", website=True)
    def leave_dl_attachment(self, attachment):
        user, employee_id = self.get_user_and_employee()
        res_id = request.env['ir.attachment'].sudo().search([("id", '=', attachment), ("res_model", '=', 'hr.holidays')], limit=1).res_id
        attachment_employee = request.env['hr.holidays'].sudo().browse(res_id).employee_id

        if employee_id.id != attachment_employee.id:
            raise ValidationError(_("This attachment is not available for this employee!"))
        return self.download_attachment(attachment)

    @http.route(['/my/leaves/submit/<int:leave>'], type='http', auth="user", website=True)
    def leave_submit(self, leave):
        user, employee_id = self.get_user_and_employee()

        if leave:
            leave_id = request.env['hr.holidays'].sudo().search([("id", '=', leave), ("employee_id", '=', employee_id.id)])
            if not leave_id:
                raise ValidationError(_("This leave does not exist!"))
            leave_id.update({
                'state': 'confirm'
            })
        return request.redirect('/my/leaves')

    @http.route(['/my/timesheets'], type='http', auth="user", website=True)
    def _prepare_portal_layout_timesheets_values(self):
        user, employee_id = self.get_user_and_employee()

        timesheets = request.env['hr_timesheet.sheet'].sudo().search([("employee_id", '=', employee_id.id)], order="date_start desc")
        values = {
            'timesheets': timesheets,
            'page_name': 'my_timesheets',
            'help_text': user.company_id.portal_help_timesheet_list_view if user.company_id.portal_help_timesheet_list_view else '',
        }
        return request.render("portal_consultant.portal_my_timesheets", values)

    @http.route(['/my/timesheets/form/<int:timesheet>'], type='http', auth="user", website=True)
    def timesheet_form(self, timesheet, m=None):
        user, employee_id = self.get_user_and_employee()

        if not user.timesheet_current_project_project_id_related or not user.timesheet_current_project_task_id_related:
            raise ValidationError(_("You must select a project and a task for this employee!"))

        default_project = user.timesheet_current_project_project_id_related
        default_task = user.timesheet_current_project_task_id_related
        if not default_project or not default_task:
            raise ValidationError(_("There is no default project or no default task set on the employee!"))

        values = {
            'page_name': 'my_timesheets_form',
            'user': user,
            'res_cal': user.resource_calendar_id,
            'WEEKDAY_TO_NAME': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
            'project_projects': request.env['project.project'].sudo().search(
                [("portal_selectable", '=', True), ("id", '!=', default_project.id)]),
            'project_1': default_project,
            'task_1': default_task,
            'help_text': user.company_id.portal_help_timesheet_form_view if user.company_id.portal_help_timesheet_form_view else '',
        }

        if timesheet != -1:
            timesheet_id = request.env['hr_timesheet.sheet'].sudo().search([("id", '=', timesheet), ("employee_id", '=', employee_id.id)])
            if timesheet_id:
                values.update({
                    'timesheet_id': timesheet_id,
                })
                attachments = request.env['ir.attachment'].sudo().search([("res_id", '=', timesheet_id.id), ("res_model", '=', 'hr_timesheet.sheet')])

                if attachments:
                    values.update({'attachments': attachments})
            else:
                return request.render('website.404')
        if m:
            values.update({'info': m}) # TODO WTF IS THIS?
        return request.render("portal_consultant.portal_form_timesheet", values)

    @http.route(['/my/timesheets/edit'], type='http', auth="user", method=['POST'], website=True)
    def timesheet_new(self, **post):
        try:
            user, employee_id = self.get_user_and_employee()

            timesheet_2 = False
            
            if 'timesheet_task_2' not in post:
                post['timesheet_task_2'] = ""

            # Check values
            if 'timesheet_start_date' not in post \
                    or 'timesheet_end_date' not in post \
                    or 'timesheet_project_2' not in post \
                    or 'timesheet_task_2' not in post \
                    or not user:
                return request.render('website.404')
            if not user.employee_ids or len(user.employee_ids) > 1:
                raise ValidationError(_("The user must be link to one and only one employee!"))
            default_project = user.timesheet_current_project_project_id_related
            default_task = user.timesheet_current_project_task_id_related
            if not default_project or not default_task:
                raise ValidationError(_("There is no default project or no default task set on the employee!"))

            # Check task errors
            if post['timesheet_project_2'] and not post['timesheet_task_2']:
                return request.redirect('/my/timesheets/form/' + post['timesheet_id'] + "?m=" + _("Please select a task for your second project !"))
            if post['timesheet_task_2'] and not post['timesheet_project_2']:
                return request.redirect('/my/timesheets/form/' + post['timesheet_id'] + "?m=" + _(
                    "Please select a project for your second task !"))
            if post['timesheet_task_2'] and post['timesheet_project_2']:
                timesheet_2 = True

            if timesheet_2:
                project2 = int(post['timesheet_project_2'])
                task2 = int(post['timesheet_task_2'])

            # EDIT
            if 'timesheet_id' in post and post['timesheet_id']:
                # TIMESHEET_SHEET UPDATE
                sheet = int(post['timesheet_id'])
                sheet_id = request.env['hr_timesheet.sheet'].sudo().search([("id", '=', sheet), ("employee_id", '=', employee_id.id)])
                if not sheet_id:
                    raise ValidationError(_("There is no matching sheet with id %s") % sheet)

                for key, value in post.items():
                    vals = {}
                    date_str = False
                    timesheet_id = False
                    if 'main-task-unit-amount_' in key:
                        date_str = key.replace('main-task-unit-amount_', '')
                        timesheet_id = self.get_or_create_timesheet(sheet_id, user, default_project.id, default_task.id,
                                                                    date_str)
                    elif timesheet_2 and 'second-task-unit-amount_' in key:
                        date_str = key.replace('second-task-unit-amount_', '')
                        timesheet_id = self.get_or_create_timesheet(sheet_id, user, project2, task2, date_str)
                    if date_str:
                        if not value:
                            value = "00:00"
                        if value and not self.is_correct_time_format(value):
                            return request.redirect('/my/timesheets/form/%s?m=%s' % (sheet_id.id, _("You must enter a correct format for hour. Wrong format: %s") % value))
                        unit_amount = self.conv_time_float(value)
                        if unit_amount != timesheet_id.unit_amount:
                            vals.update({
                                'unit_amount': unit_amount,
                            })
                    if vals and timesheet_id:
                        timesheet_id.write(vals)

                if 'timesheet_file' in post and post.get('timesheet_file'):
                    attachments = request.env['ir.attachment']
                    name = post.get('timesheet_file').filename
                    file = post.get('timesheet_file')
                    attachment = file.read()
                    attachment_id = attachments.sudo().create({
                        'name': name,
                        'datas_fname': name,
                        'type': 'binary',
                        'res_model': 'hr_timesheet.sheet',
                        'res_id': sheet_id.id,
                        'datas': base64.b64encode(attachment),
                    })
            else:
                # TIMESHEET_SHEET CREATION
                name = self._compute_name(post['timesheet_start_date'])
                if self.is_overlapped(post['timesheet_start_date'], post['timesheet_end_date']):
                    values = self._prepare_values(user, default_project, default_task, _("Overlapping"))
                    return request.render("portal_consultant.portal_form_timesheet", values)
                elif self.is_date_end_before_date_start(post['timesheet_start_date'], post['timesheet_end_date']):
                    values = self._prepare_values(user, default_project, default_task, _("Your start date is after your end date"))
                    return request.render("portal_consultant.portal_form_timesheet", values)
                else:
                    vals = {
                        'date_start': post['timesheet_start_date'],
                        'date_end': post['timesheet_end_date'],
                        'employee_id': employee_id.id,
                        'name': name,
                        'state': 'draft',
                        'company_id': employee_id.company_id.id,
                    }
                    if timesheet_2:
                        vals.update({
                            'timesheet_project_2': project2,
                            'timesheet_task_2': task2,
                        })
                    sheet_id = request.env['hr_timesheet.sheet'].sudo().create(vals)
                    if 'timesheet_file' in post and post.get('timesheet_file'):
                        attachments = request.env['ir.attachment']
                        name = post.get('timesheet_file').filename
                        file = post.get('timesheet_file')
                        attachment = file.read()
                        attachment_id = attachments.sudo().create({
                            'name': name,
                            'datas_fname': name,
                            'type': 'binary',
                            'res_model': 'hr_timesheet.sheet',
                            'res_id': sheet_id.id,
                            'datas': base64.b64encode(attachment),
                        })

            if 'submit' not in post:
                # BUTTON SAVE
                return request.redirect('/my/timesheets/form/%d' % sheet_id.id)
            else:
                # BUTTON SUBMIT
                sheet_id.write({'state': 'confirm'})
                return request.redirect('/my/timesheets')
        except (UserError, ValidationError) as e:
            return request.render("portal.portal_my_home", {'info': e.args})

    @http.route(['/my/timesheets/delete/<int:timesheet>'], type='http', auth="user", website=True)
    def timesheet_delete(self, timesheet):
        user, employee_id = self.get_user_and_employee()
        if timesheet:
            timesheet_sheet = request.env['hr_timesheet.sheet'].sudo().search([("id", '=', timesheet), ("employee_id", '=', employee_id.id)])
            for aal in timesheet_sheet.timesheet_ids:
                aal.unlink()
            timesheet_sheet.unlink()

        return request.redirect('/my/timesheets')

    @http.route(['/my/timesheets/pdf/<int:timesheet>'], type='http', auth="user", website=True)
    def portal_timesheet_report(self, timesheet, access_token=None, **kw):
        user, employee_id = self.get_user_and_employee()
        # TODO Check that this sheet belongs to the current employee DONE
        sheet = request.env['hr_timesheet.sheet'].sudo().search([('id', '=', timesheet), ('employee_id', '=', employee_id.id)])
        if not sheet:
            raise ValidationError(_("This sheet doesn't exist or you don't have permission to check others sheets."))
        template = request.env.ref('hr_timesheet_report.hr_timesheet_print_report').sudo()
        pdf = template.render_qweb_pdf([timesheet])[0]
        pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]

        response = request.make_response(pdf, headers=pdfhttpheaders)
        response.headers.add('Content-Disposition', 'attachment; filename=%s.pdf;' % 'Timesheet_Report')
        return response

    @http.route(['/my/timesheets/submit/<int:timesheet>'], type='http', auth="user", website=True)
    def timesheet_submit(self, timesheet):
        user, employee_id = self.get_user_and_employee()

        if timesheet:
            tss = request.env['hr_timesheet.sheet'].sudo().search([("id", '=', timesheet), ("employee_id", '=', employee_id.id)])
            if not tss:
                raise ValidationError(_("There is a no timesheet sheet with this ID for this employee"))
            tss.write({
                'state': 'confirm'
            })
        return request.redirect('/my/timesheets')

    @http.route(['/my/timesheets/delete/attachment/<int:attachment>'], type='http', auth="user", website=True)
    def timesheet_delete_attachment(self, attachment):
        user, employee_id = self.get_user_and_employee()
        if not attachment:
            raise ValidationError(_("There is no attachment for this timesheet sheet!"))
        attachment = request.env['ir.attachment'].sudo().search([("id", '=', attachment), ("res_model", '=', 'hr_timesheet.sheet')])
        sheet_id = attachment.res_id
        sheet = request.env['hr_timesheet.sheet'].sudo().search([('id', '=', sheet_id), ('employee_id', '=', employee_id.id)])
        if not sheet:
            raise ValidationError(_("Attachment doesn't exist or it's not yours.")) 
        attachment.sudo().unlink()
        if sheet_id:
            return request.redirect('/my/timesheets/form/' + str(sheet_id))
        else:
            return request.redirect('/my/timesheets')

    @http.route(['/my/timesheets/download/attachment/<int:attachment>'], type='http', auth="user", website=True)
    def timesheet_dl_attachment(self, attachment):
        user, employee_id = self.get_user_and_employee()
        res_id = request.env['ir.attachment'].sudo().search([("id", '=', attachment), ("res_model", '=', 'hr_timesheet.sheet')], limit=1).res_id
        attachment_employee = request.env['hr_timesheet.sheet'].sudo().browse(res_id).employee_id

        if employee_id.id != attachment_employee.id:
            raise ValidationError(_("This attachment is not available for this employee!"))
        return self.download_attachment(attachment)
