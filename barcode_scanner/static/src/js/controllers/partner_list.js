odoo.define('barcode_scanner.PartnerList', function(require){

    var ajax = require("web.ajax");
    var core = require("web.core");
    var router = require('barcode_scanner.router');
    var Widget = require("web.Widget");
    var qweb = core.qweb;

    var PartnerList = Widget.extend({
        template:"barcode_scanner.partner_list",
        xmlDependencies: ['/barcode_scanner/static/src/xml/partner_list_view.xml'],
        events: {
            'click .thumbnail': function(ev){
                var partner_key = $(ev.currentTarget).data("key");
                router.navigate("/partner/" + partner_key);
            },
            'click #partner_search_button': function(ev){
                ev.preventDefault();
                this._search_button_handler();
            },
            'click #home_breadcrumb':function(ev){
                router.navigate("/home");
            },
            'keyup #partner_search_input': function(ev){
                var code = (ev.keyCode ? ev.keyCode : ev.which);
                if(code === 13 || ev.currentTarget.value === ""){
                    this._search_button_handler();
                }
                if(code === 13){
                    $("#partner_search_input").blur();
                }
            },
            'change :checkbox': function(ev){
                var value = $(ev.currentTarget).val();
                
                if (value === 'is_customer')
                    this.is_customer = ev.target.checked;
                else if (value === 'is_vendor')
                    this.is_vendor = ev.target.checked;
                else if (value === 'is_employee')
                    this.is_employee = ev.target.checked;
                else if (value === 'is_company')
                    this.is_company = ev.target.checked;
                
                this._search_button_handler();
                $("#partner_search_input").blur();
            },
            'click .li-page': function(ev){
                this.page = parseInt(ev.target.textContent);
                this._get_partners_and_rerender();
            },
            'click #li-next': function(ev){
                this.page += 1;
                this._get_partners_and_rerender();
            },
            'click #li-prev': function(ev){
                this.page -= 1;
                this._get_partners_and_rerender();
            },
        },
        /* Lifecycle */
        init: function(parent){
            this._super.apply(this, arguments);
            this.parent = parent;
            this.properties_for_filter = ['name'];

            this.is_company = true;
            this.is_customer = true;
            this.is_employee = true;
            this.is_vendor = true;
            
            this.partners = [];
            this.partners_to_display = [];
            this.page = 1;
        },
        willStart: function(){
            var self = this;
            self.trigger_up("loading", {loading: true});
            let values = {
                token: self.parent.user.token,
                page: self.page, 
                is_company: self.is_company, 
                is_customer: self.is_customer, 
                is_employee: self.is_employee,
                is_vendor: self.is_vendor
            }
            return $.when(this._super.apply(this, arguments),
            ajax.jsonRpc('/barcode_scanner/get/partners', 'call', values))
            .done((args1, args2) => {
                if(args2.hasOwnProperty("error")){
                    self.trigger_up('checkIfTokenExpired', {value: args2});
                }
                self.partners = args2.result.partners;
                self.partners_to_display = args2.result.partners;
                self.total_pages = args2.result.total_pages;
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
        
        _get_partners_and_rerender: function(){
            var self = this;
            self.trigger_up("loading", {loading: true});
            let values = {
                token: self.parent.user.token,
                page: self.page, 
                is_company: self.is_company, 
                is_customer: self.is_customer, 
                is_employee: self.is_employee,
                is_vendor: self.is_vendor,
                search_text: self.search_text,
            }
            
            ajax.jsonRpc('/barcode_scanner/get/partners', 'call', values)
                .then((data) => {
                    if(data.hasOwnProperty("error")){
                        self.trigger_up('checkIfTokenExpired', {value: data});
                    }
                    self.partners = data.result.partners;
                    self.partners_to_display = data.result.partners;
                    self.total_pages = data.result.total_pages;
                    self._rerender();
                    self.trigger_up("loading", {loading: false});
                });
        },

        // Handlers
        _search_button_handler: function(){
            var self = this;
            self.search_text = $("#partner_search_input").val();
            self._get_partners_and_rerender();
            
            self._rerender();
            $("#partner_search_input").focus().val('').val(self.search_text);
        },

        // Render method
        _rerender: function () {
            this.replaceElement(qweb.render('barcode_scanner.partner_list', {widget: this}));
        },
    });

    return PartnerList;

})