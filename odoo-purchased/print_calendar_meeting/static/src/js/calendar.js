odoo.define('print_calendar_meeting.calendar', function (require) {
"use strict";

var CalendarController = require('web.CalendarController');
//var CalendarView = require('web.CalendarView');
var core = require('web.core');
var _t = core._t;
//var CalendarController = CalendarView.include({
//    render_buttons: function($node) {
CalendarController.include({
    renderButtons: function ($node) {
        var self = this;
        this._super($node);
        this.$buttons.on('click', 'button.o_calendar_button_report', function () {
            var action = {
                type: 'ir.actions.act_window',
                res_model: 'calendar.meeting.report',
                view_mode: 'form',
                view_type: 'form',
                views: [[false, 'form']],
                name: _t('Print Calendar'),
                target: 'new',
                context: {},
            };
            self.do_action(action, {
                on_close: function () {
                },
            });
        })
    }
})
})
