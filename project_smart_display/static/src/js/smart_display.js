function startTime() {
    var today = new Date();
    var d = today.getDate();
    var M = today.getMonth();
    var y = today.getFullYear();
    var h = today.getHours();
    var m = today.getMinutes();
    var s = today.getSeconds();
    m = _checkTime(m);
    s = _checkTime(s);
    document.getElementById('date_time_clock').innerHTML = d + "/" + M + "/" + y + " " + h + ":" + m + ":" + s;
    var t = setTimeout(startTime, 500);
}

function _checkTime(i) {
    if (i < 10) {i = "0" + i};  // add zero in front of numbers < 10
    return i;
}

var delay = ( function() {
    var timer = 0;
    return function(callback, ms) {
        clearTimeout (timer);
        timer = setTimeout(callback, ms);
    };
})();

function startPageManager() {
    odoo.define('project_smart_display.smart_display_viewing', ['web.ajax'], function (require) {
        "use strict";
        var ajax = require('web.ajax');

        var display_id = parseInt($("#display_id").text());

        var page_count = parseInt($("#page_count").text());
        var display_delay = parseInt($("#display_delay").text());
        
        // Get first page
        delay(function(){
            ajax.jsonRpc("/smartdisplay/getdisplay/", 'call', {
                'display_id': display_id,
            }).then(function (data_display) {
                if(data_display){
                    if(data_display['show_telephony'] == true) {
                        _handleTelephony(data_display['callflows']);
                    }
                    
                    // Set the count
                    page_count = parseInt(data_display['page_count']);
                    $("#page_count").text(page_count);

                    // Set the delay
                    $("#display_delay").text(parseInt(data_display['display_delay']));

                    ajax.jsonRpc("/smartdisplay/getnextpage/", 'call', {
                        'display_id': data_display['display_id'],
                        'index': 0,
                    }).then(function (data_page) {
                        if(data_page){
                            if (data_page['mode'] == 'iframe') {
                                document.getElementById('smart_dashboard').style.display = "none";
                                document.getElementById('page_iframe').setAttribute('src', data_page['iframe_url']);
                                document.getElementById('page_iframe').style.display = "inline";
                            }
                            if (data_page['mode'] == 'smart_dashboard') {
                                document.getElementById('page_iframe').style.display = "none";
                                document.getElementById('smart_dashboard').innerHTML = data_page['smart_dashboard_html'];
                                document.getElementById('smart_dashboard').style.display = "inline";
                            }
                        }
                    })
                }
            })
        });

        setInterval(function() { counter() }, display_delay * 1000); // Multiplied by 1000 because this method wants microseconds and we manage seconds

        function counter() {
            var index = parseInt($("#page_index").text());

            // Get page for index
            ajax.jsonRpc("/smartdisplay/getnextpage/", 'call', {
                'display_id': display_id,
                'index': index,
            }).then(function (data_page) {
                if(data_page){
                    // Set the count
                    page_count = parseInt(data_page['display_page_count']);
                    $("#page_count").text(page_count);

                    // If iframe, set the frame
                    if (data_page['mode'] == 'iframe') {
                        document.getElementById('page_iframe').setAttribute('src', data_page['iframe_url']);
                        document.getElementById('page_iframe').style.display = "inline";
                    }
                    // If smart dashboard, set the board
                    if (data_page['mode'] == 'smart_dashboard') {
                        document.getElementById('page_iframe').style.display = "none";
                        document.getElementById('smart_dashboard').innerHTML = data_page['smart_dashboard_html'];
                        document.getElementById('smart_dashboard').style.display = "inline";
                    }
                }
            })

            // Increase index
            if (index < page_count) {
                index = index + 1;
            }
            else {
                index = 1;
            }
            $("#page_index").text(index);
        }
    });
}

function _handleTelephony(callflows) {
    let userAgent = new SIP.UA({
        uri: 'sip:abakus-office.7tmm38eq@abakus-office.allocloud.com',
        transportOptions: {
            wsServers: ['wss://abakus-office.allocloud.com/v3.0/websockets/sip'],
        },
        authorizationUser: 'abakus-office.7tmm38eq',
        password: 'nOn1RzwJL3wrlDugztA'
    });

    let contactListObj = [];
    for(var property in callflows){
        let name = ''
        if (property.startsWith('EXT_')){
            name = property.substring(property.indexOf('_') + 1).substring(property.indexOf('_'));
        } else {
            name = property.substring(property.indexOf('_') + 1);
        }
        contactListObj.push({name:name, callId:callflows[property], status:""});
    }

    userAgent.removeAllListeners('notify'); // avoids memory leak
    userAgent.setMaxListeners(15);
    let subscription = null;
    contactListObj.sort((a, b) => (a.name > b.name) ? 1 : -1) // sort list by name ASC
    contactListObj.forEach((contactObj) => {
        subscription = userAgent.subscribe(contactObj.callId + '@abakus-office.allocloud.com', 'presence');

        subscription.on('notify', function (notification) {
            _generateTelephonyContacts(notification, contactObj);
        });
    });
}

function _generateTelephonyContacts(notification, contactObj) {
            let parser = new DOMParser();
            let xmlDoc = parser.parseFromString(notification.request.body, "text/xml");
            let contact_status = xmlDoc.getElementsByTagName("basic")[0].childNodes[0].nodeValue;
            if (xmlDoc.getElementsByTagName("rpid:on-the-phone").length !== 0){
                contact_status = "on the phone";
            }
            contactObj.status = contact_status;

            if (contactObj.status === "open") {
                if (document.getElementById(contactObj.callId) != null) {
                    document.getElementById(contactObj.callId).className  = "contact_status contact_online";
                } else {
                    document.getElementById("contacts_status").innerHTML += "<div id='" + contactObj.callId + "' class='contact_status contact_online'>" + contactObj.name + "</div>";
                    document.getElementById("contacts_id").innerHTML += "<div class='contact_id'>" + contactObj.callId + "</div>";
                }
            } else if (contactObj.status === "on the phone") {
                if (document.getElementById(contactObj.callId) != null) {
                    document.getElementById(contactObj.callId).className  = "contact_status contact_on_phone";
                } else {
                    document.getElementById("contacts_status").innerHTML += "<div id='" + contactObj.callId + "' class='contact_status contact_on_phone'>" + contactObj.name + "</div>";
                    document.getElementById("contacts_id").innerHTML += "<div class='contact_id'>" + contactObj.callId + "</div>";
                }
            } else if (contactObj.status === "closed") {
                if (document.getElementById(contactObj.callId) != null) {
                    document.getElementById(contactObj.callId).className  = "contact_status contact_offline";
                } else {
                    document.getElementById("contacts_status").innerHTML += "<div id='" + contactObj.callId + "' class='contact_status contact_offline'>" + contactObj.name + "</div>";
                    document.getElementById("contacts_id").innerHTML += "<div class='contact_id'>" + contactObj.callId + "</div>";
                }
            }
}