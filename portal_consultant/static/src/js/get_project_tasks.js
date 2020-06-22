odoo.define('portal_consultant.get_project_tasks', function (require) {
    "use strict";

    var ajax = require("web.ajax");

    let project2 = document.getElementById('timesheet_project_2');
    project2.addEventListener('change', function(e){
        onchange_project(e);
    });
    project2.dispatchEvent(new Event('change'));

    let task2 = document.getElementById('timesheet_task_2');
    task2.addEventListener('change', function(e){
        onchange_task(e);
    })
    task2.dispatchEvent(new Event('change'));

    function onchange_project(e) {
        let value = null;
        if (e.target.value === ""){
            $("#timesheet_task_2").empty();
            $('label[for="timesheet_task_2"]').hide();
            $("#timesheet_task_2").hide();
            $("#timesheet_task_2_display").hide();
        }else{
            $('label[for="timesheet_task_2"]').show();
            $("#timesheet_task_2").show();
            value = e.target.value;
            let url = "/my/get_project_tasks/" + value
            ajax.jsonRpc(url, 'call', {})
                .then(function(data){
                    $("#timesheet_task_2").empty();
                    let tasks = data.result;
                    var option = document.createElement("option");
                    option.text = "";
                    option.value = "";
                    task2.add(option);
                    tasks.forEach(element => {
                        var option = document.createElement("option");
                        option.text = element.name;
                        option.value = element.id;
                        option.id = element.id;
                        task2.add(option);
                    });
                })
        }
    }
    
    $('th').each(function(){
        console.log($(this).attr('name'))
    })
    
    function onchange_task(e) {
        let value = null;
        let elements = $('table > tbody > tr > td > input')
        if (e.target.value === ""){
            $('th').each(function(){
                    if($(this).html().includes("Second") || ($(this).attr('name') != undefined && $(this).attr('name').includes("second"))){
                    console.log($(this).name)
                   $(this).hide()
                }
            });
            Array.from(elements).forEach((el) => {
                if (el.name.includes("second-task")){
                    el.parentNode.style.display='none';
                }
            })

        }else{
            $('th').each(function(){
                if($(this).html().includes("Second") || ($(this).attr('name') != undefined && $(this).attr('name').includes("second"))){
                    console.log($(this).name)
                   $(this).show()
                }
            });
            Array.from(elements).forEach((el) => {
                if (el.name.includes("second-task")){
                    el.parentNode.style.display='display';
                }
            })
        }
    }
});