odoo.define('portal_consultant.compute_leaves_date', ['web.ajax'], function (require) {
    "use strict";

    var ajax = require("web.ajax");

    let start_date = document.getElementById('leave_start_date');
    start_date.addEventListener('change', function(e){
        dateonchange(e);
    });
    let end_date = document.getElementById('leave_end_date');
    end_date.addEventListener('change', function(e){
        dateonchange(e);
    });
    let start_moment = document.getElementById('leave_start_moment');
    start_moment.addEventListener('change', function(e){
        dateonchange(e);
    });
    let end_moment = document.getElementById('leave_end_moment');
    end_moment.addEventListener('change', function(e){
        dateonchange(e);
    });
    let number_days = document.getElementById('leave_number_of_days');

    function dateonchange(event) {
        let body = {
            start_date: leave_start_date.value,
            end_date: leave_end_date.value,
            start_moment : leave_start_moment.value,
            end_moment: leave_end_moment.value
        };
        console.log(body);
        ajax.jsonRpc("/my/check_date", 'call', body)
            .then(function(data){
                number_days.value = data.result.number_of_days
            })

    }
});