odoo.define('barcode_scanner.views', function (require) {
    'use strict';

    var core = require('web.core');
    var Widget = require('web.Widget');
    var notification = require("web.notification");
    var router = require('barcode_scanner.router');

    // All Barcode Scanner Interface Pages
    var Product = require('barcode_scanner.Product');
    var Location = require('barcode_scanner.Location');
    var Home = require("barcode_scanner.Home");
    var UserList = require("barcode_scanner.UserList");
    var Picking = require("barcode_scanner.Picking");
    var IncommingProcess = require("barcode_scanner.IncommingProcess")
    var ProductList = require("barcode_scanner.ProductList");
    var PartnerList = require("barcode_scanner.PartnerList");
    var Partner = require("barcode_scanner.Partner");
    var PartnerTransfer = require("barcode_scanner.PartnerTransfer");
    var PickingList = require("barcode_scanner.PickingList");
    var PartnerPicking = require("barcode_scanner.PartnerPicking");
    var Inventory = require("barcode_scanner.Inventory");

    var qweb = core.qweb;

    require('web.dom_ready'); // Wait for the dom to be ready

    var ScannerApp = Widget.extend({
        template: 'barcode_scanner.app',
        events: {
            'click #home_title': function(ev){
                ev.preventDefault();
                router.navigate('/home');
            },
            'click #home_nav_button': function(ev){
                ev.preventDefault();
                router.navigate('/home');
            },
            'click #product_list_nav_button': function(ev){
                ev.preventDefault();
                router.navigate('/products');
            },
            'click #partner_list_nav_button': function(ev){
                ev.preventDefault();
                router.navigate('/partners');
            },
            'click #logout_nav_button': function(ev){
                router.navigate("/logout");
            },
            'click #inventory_nav_button': function(ev){
                router.navigate("/inventory");
            }
        },
        custom_events: {
            'warning': function (ev) {this.notification_manager.warn(ev.data.msg);},
            'notify': function (ev) {this.notification_manager.notify(ev.data.msg);},
            'loading': function(ev) {this._loading(ev.data.loading)},
            'checkIfTokenExpired': function(ev){
                if(ev.data.value.error.hasOwnProperty("logout")){
                    if(ev.data.value.error.logout){
                        router.navigate("/logout");
                    }
                    this.trigger_up("warning", {msg: (ev.data.value.error.message)});
                }
            }
        },
        xmlDependencies: ['/barcode_scanner/static/src/xml/app_view.xml'],
        /* Lifecycle */
        init: function (parent, options) {
            this._super.apply(this, arguments);
            var self = this;
            self.widget = null;
            self.loggedIn = false;
            
            // router config
            router.config({ mode: 'history', root:'/barcode_scanner'});
    
            // adding routes
            router
            .add(/login/, function () {
                self._destroyWidget();
                self._login();
            }).add(/product\/(.*)\/incomming\/step\/(.*)/, function(){
                self._destroyWidget();
                self._incomming_process(arguments[0], parseInt(arguments[1])); // arguments[0] = first (.*) found with regex
                self._resetUserCookie();
            }).add(/product\/(.*)\/picking-in\/(.*)/, function(){
                self._destroyWidget();
                self._product_picking(arguments[0], arguments[1], 'in'); // arguments[0] = first (.*) found with regex
                self._resetUserCookie();
            }).add(/product\/(.*)\/picking-out\/(.*)/, function(){
                self._destroyWidget();
                self._product_picking(arguments[0], arguments[1], 'out'); // arguments[0] = first (.*) found with regex
                self._resetUserCookie();
            }).add(/product\/(.*)\/in/, function(){
                self._destroyWidget();
                self._product(arguments[0], 'in'); // arguments[0] = first (.*) found with regex
                self._resetUserCookie();
            }).add(/product\/(.*)\/out/, function(){
                self._destroyWidget();
                self._product(arguments[0], 'out'); // arguments[0] = first (.*) found with regex
                self._resetUserCookie();
            }).add(/product\/(.*)/, function(){
                self._destroyWidget();
                self._product(arguments[0]); // arguments[0] = first (.*) found with regex
                self._resetUserCookie();
            }).add(/products/, function(){
                self._destroyWidget();
                self._product_list();
                self._resetUserCookie();
            }).add(/partner\/(.*)\/sell/, function(){
                self._destroyWidget();
                self._partner_sell(arguments[0]); // arguments[0] = first (.*) found with regex
                self._resetUserCookie();
            }).add(/partner\/(.*)\/outgoings/, function(){
                self._destroyWidget();
                self._partner_outgoings(arguments[0]); // arguments[0] = first (.*) found with regex
                self._resetUserCookie();
            }).add(/partner\/(.*)\/picking\/(.*)/, function(){
                self._destroyWidget();
                self._outgoing_picking(arguments[1], arguments[0]); // arguments[0] = first (.*) found with regex
                self._resetUserCookie();
            }).add(/partner\/(.*)/, function(){
                self._destroyWidget();
                self._partner(arguments[0]); // arguments[0] = first (.*) found with regex
                self._resetUserCookie();
            }).add(/partners/, function(){
                self._destroyWidget();
                self._partner_list();
                self._resetUserCookie();
            }).add(/inventory/, function(){
                self._destroyWidget();
                self._inventory();
                self._resetUserCookie();
            }).add(/logout/, function(){
                self._destroyWidget();
                self._logout();
            }).add(/location\/(.*)/, function(){
                self._destroyWidget();
                self._location(arguments[0]); // arguments[0] = first (.*) found with regex
                self._resetUserCookie();
            }).add(/home/,function(){
                self._destroyWidget();
                self._home();
                self._resetUserCookie();
            }).add(function(){
                self._destroyWidget();
                router.navigate('/home');
            })
            .listen();

        },
        willStart: function () {
            var self = this;
            return $.when(this._super.apply(this, arguments)
            ).done(function(arg1){
                if(Cookies.get("user") != undefined){
                    self.loggedIn = true;
                }
            })
        },
        start: function () {
            var self = this;
            return $.when(this._super.apply(this, arguments)).then(function () {
                self.notification_manager = new notification.NotificationManager();
                self.notification_manager.appendTo(document.body);
                let cookie = Cookies.get("user")
                self._resetUserCookie();
                if(cookie != undefined){
                    self.user = JSON.parse(cookie);
                    router.check();
                }else{
                    if(router.getFragment() == 'barcode_scanner/login'){
                        router.check();
                    }
                    else{
                        router.navigate("/login")
                    }
                }
            });
        },
        // Handlers for all routes
        _home: function(){
            if(!this._cookie_expired())
                return;
            this.widget = new Home(this);
            this.widget.appendTo($(".barcode_scanner_app"));
        },
        _incomming_process: function(product_key, step){
            if(!this._cookie_expired())
                return;
            this.widget = new IncommingProcess(this, product_key, step);
            this.widget.appendTo($(".barcode_scanner_app"));
            
        },
        _product: function(barcode, operation_name){
            if(!this._cookie_expired())
                return;
            this.widget = new Product(this, barcode, operation_name);
            this.widget.appendTo($(".barcode_scanner_app"))
        },
        _product_picking: function(product_key, picking_key, operation_type){
            if(!this._cookie_expired())
                return;
            this.widget = new Picking(this, product_key, picking_key, operation_type);
            this.widget.appendTo($(".barcode_scanner_app"));
        },
        _login: function(){
            let cookie = Cookies.get("user");
            if(cookie != undefined){

            }else{
                this.widget = new UserList(this, this.users);
                this.widget.appendTo($(".barcode_scanner_app"))
            }
        },
        _inventory: function(){
            if(!this._cookie_expired())
                return;
            this.widget = new Inventory(this);
            this.widget.appendTo(".barcode_scanner_app");
        },
        _location: function(barcode){
            if(!this._cookie_expired())
                return;
            this.widget = new Location(this, barcode);
            this.widget.appendTo($(".barcode_scanner_app"));
        },
        _product_list: function(){
            if(!this._cookie_expired())
                return;
            this.widget = new ProductList(this);
            this.widget.appendTo($(".barcode_scanner_app"));
        },
        _partner: function(partner_key){
            if(!this._cookie_expired())
                return;
            this.widget = new Partner(this, partner_key);
            this.widget.appendTo($(".barcode_scanner_app"));
        },
        _partner_sell: function(partner_key){
            if(!this._cookie_expired())
                return;
            this.widget = new PartnerTransfer(this, partner_key);
            this.widget.appendTo($(".barcode_scanner_app"));
        },
        _partner_list: function(){
            if(!this._cookie_expired())
                return;
            this.widget = new PartnerList(this);
            this.widget.appendTo($('.barcode_scanner_app'));
        },
        _partner_outgoings: function(partner_key){
            if(!this._cookie_expired())
                return;
            PickingList = PickingList.extend({
                events: _.extend({}, PickingList.prototype.events,{
                    'click .list-group-item': function(ev){
                        router.navigate("/partner/"+ partner_key + "/picking/" + $(ev.currentTarget).data("id"));
                    }
                })
            })
            this.widget = new PickingList(this, partner_key, 'out', "partner");
            this.widget.appendTo($('.barcode_scanner_app'));
        },
        _outgoing_picking: function(picking_key, partner_key){
            if(!this._cookie_expired())
                return;
            this.widget = new PartnerPicking(this, picking_key, partner_key);
            this.widget.appendTo($(".barcode_scanner_app"));
        },
        _logout: function(){
            Cookies.remove("user");
            this.loggedIn = false;
            this._rerender();
            router.navigate('/login');
        },

        //Rerender method for app
        _rerender: function () {
            this.replaceElement(qweb.render('barcode_scanner.app', {widget: this}));
        },

        // Util fonctions
        _loading: function(boolean){
            if(boolean)
                $("#loader").addClass("is-active");
            else
                $("#loader").removeClass("is-active");
        },
        _resetUserCookie: function(){
            let cookie = Cookies.get("user");
            if(cookie != undefined)
                Cookies.set("user", Cookies.get("user"), {expires: 0.5/24 }) // 0.5/24 = 30 minutes because expires is set in day
        },
        _cookie_expired: function(){
            if(Cookies.get("user") != null){
                this.user = JSON.parse(Cookies.get("user"));
                return true;
            }
            else{
                router.navigate("/login");
                return false;
            }
        },
        // Destroy the actual widget
        _destroyWidget: function(){
            if(this.widget != null){
                this.widget.destroy();
            }
        }

    })

    var $elem = $('.barcode_scanner_app');
    var app = new ScannerApp(null);
    app.appendTo($elem)
});