odoo.define('barcode_scanner.Partner', function(require){

    var ajax = require("web.ajax");
    var router = require('barcode_scanner.router');
    var Widget = require("web.Widget");

    var PartnerList = Widget.extend({
        template:"barcode_scanner.partner",
        xmlDependencies: ['/barcode_scanner/static/src/xml/partner_view.xml'],
        events: {
            'click #sell_button': function(ev){
                ev.preventDefault();
                this._sell_button_handler();
            },
            'click #outgoings_button': function(ev){
                ev.preventDefault();
                this._handler_for_outgoing_button();
            },
            'click #home_breadcrumb': function(ev){
                router.navigate("/home");
            },
            'click #partners_breadcrumb': function(ev){
                router.navigate("/partners");
            }
        },
        /* Lifecycle */
        init: function(parent, partner_key){
            this._super.apply(this, arguments);
            this.parent = parent;
            this.partner_key = partner_key;
            this.properties_for_filter = ['name', 'ref', 'description', 'barcode'];
        },
        willStart: function(){
            var self = this;
            self.trigger_up("loading", {loading: true});
            return $.when(this._super.apply(this, arguments),
            ajax.jsonRpc('/barcode_scanner/get/partner/', 'call', {token: self.parent.user.token, partner_key: self.partner_key, operation_type_name: 'out', unwanted_states: ["done", 'cancel']}) )
            .done((args1, args2) => {
                if(args2.hasOwnProperty("error")){
                    self.trigger_up('checkIfTokenExpired', {value: args2});
                }
                self.partner = args2.result;
            });
        },
        start: function(){
            var self = this;
            return $.when(this._super.apply(this, arguments)).then(function(){
                self.trigger_up("loading", {loading: false});
            });
        },
        destroy: function(){
            return $.when(this._super.apply(this, arguments)).then(function(){
                $(this).empty();
            });
        },
        _handler_for_outgoing_button: function(){
            router.navigate("/partner/" + this.partner_key + '/outgoings')
        },
        _sell_button_handler: function(){
            router.navigate("/partner/" + this.partner_key + "/sell");
        }
    });

    return PartnerList;

})