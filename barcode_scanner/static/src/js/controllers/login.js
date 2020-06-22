odoo.define('barcode_scanner.UserList', function(require){

    var Widget = require("web.Widget");
    var Dialog = require("web.Dialog");
    var router = require('barcode_scanner.router');
    var core = require('web.core');
    var ajax = require("web.ajax");
    var qweb = core.qweb;
    var _t = core._t;

    var UserList = Widget.extend({
        template: 'barcode_scanner.login',
        events:{
            'click .thumbnail': function(ev){
                this.email = $(ev.currentTarget).data("email");
                this._open_connection_dialog(this.email);
            }
        },
        xmlDependencies: ['/barcode_scanner/static/src/xml/login_view.xml'],
        /* Lifecycle */
        init: function (parent) {
            this._super.apply(this, arguments);
            this.parent = parent;
            this.users = [];
            this.dialog = null;
            this.email = null;
            this.pin_code = null;
        },
        willStart: function(){
            this.trigger_up("loading", {loading: true});
            return $.when(this._super.apply(this, arguments), ajax.jsonRpc('/barcode_scanner/get/users/', 'call') )
            .done((args1, args2)=>{
                this.users = args2.users;
            })
        },
        start: function(){
            return $.when(this._super.apply(this, arguments)).then(()=>{
                this.trigger_up("loading", {loading: false})
            })
        },
        destroy: function(){
            return $.when(this._super.apply(this, arguments)).then(function(){
                $(this).empty();
            });
        },
        _open_connection_dialog: function(email){
            var self = this;
            Dialog = Dialog.extend({
                events:{
                    'keydown #pin_code': function(ev){
                        self._pin_code_listener(ev);
                    }
                }
            })
            self.dialog = new Dialog(this, {
                title: _t('Connection'),
                $content: qweb.render('barcode_scanner.login.pincode'),
                buttons: [{
                    text: _t('Login'),
                    click: function () {
                        let pin_code = $("#pin_code").val();
                        self.trigger_up("loading", {loading: true})
                        self._login(email, pin_code);
                    },
                    close: false,
                }]
            })
            .open();
            $("#pin_code").focus();
        },
        _login: function(email, pin_code){
            var self = this;
            ajax.jsonRpc('/barcode_scanner/get/login/', 'call', { email: email, pin_code: pin_code})
            .then(function(data){
                if(data.hasOwnProperty('result')){
                    let user = data.result;
                    email = user.email.toLowerCase();
                    if(email != "false" && email != undefined){
                        Cookies.set('user', JSON.stringify(user), {expires: 0.5/24}) // 0.5/24 = 30 minutes because expires is set in day
                        self.parent.user = user;
                        self.dialog.close();
                        self.parent.loggedIn = true;
                        self.parent._rerender();
                        router.navigate('/home');
                    }
                }else if(data.hasOwnProperty('error')){
                    $("#pin_code").focus();
                    self.trigger_up("warning", {msg: _t(data.error.message)})
                }
                self.trigger_up("loading", {loading: false})
            })
        },
        _pin_code_listener: function(e){
            var code = (e.keyCode ? e.keyCode : e.which);
            if(code==13){
                let pin_code = $("#pin_code").val();
                this._login(this.email, pin_code);
            }
        }

    })

    return UserList;

})