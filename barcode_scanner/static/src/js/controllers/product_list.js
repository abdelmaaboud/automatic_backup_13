odoo.define('barcode_scanner.ProductList', function (require){
    'use strict';

    var ajax = require("web.ajax");
    var Widget = require('web.Widget');
    var core = require('web.core');
    var qweb = core.qweb;

    var router = require("barcode_scanner.router");

    var ProductList = Widget.extend({
        template:"barcode_scanner.product_list",
        xmlDependencies: ['/barcode_scanner/static/src/xml/product_list_view.xml'],
        events: {
            'click #product_search_button': function(ev){
                ev.preventDefault();
                this._search_button_handler();
            },
            'keyup #product_search_input': function(ev){
                var code = (ev.keyCode ? ev.keyCode : ev.which);
                if(code === 13 || ev.currentTarget.value === ""){
                    this._search_button_handler();
                }
                if(code === 13){
                    $("#partner_search_input").blur();
                }
            },
            'click .thumbnail': function(ev){
                var product_key = null;
                if($(ev.currentTarget).data("name") != "")
                    product_key = $(ev.currentTarget).data("name");
                else if($(ev.currentTarget).data("barcode") != "")
                    product_key = $(ev.currentTarget).data("barcode");
                else if($(ev.currentTarget).data("id") != "")
                    product_key = $(ev.currentTarget).data("id")
                router.navigate("/product/" + product_key);
            },
            "click #home_breadcrumb": function(ev){
                router.navigate("/home");
            },
            'change #product_available_checkbox': function(ev){
                this.show_available_products = ev.target.checked;
                this._get_products_and_rerender();
                this._rerender();
            },
            'change #product_unavailable_checkbox': function(ev){
                this.show_unavailable_products = ev.target.checked;
                this._get_products_and_rerender();
                this._rerender();
            },
            'click .li-page': function(ev){
                this.page = parseInt(ev.target.textContent);
                this._get_products_and_rerender();
            },
            'click #li-next': function(ev){
                this.page += 1;
                this._get_products_and_rerender();
            },
            'click #li-prev': function(ev){
                this.page -= 1;
                this._get_products_and_rerender();
            },
        },
        /* Lifecycle */
        init: function(parent, is_page=true){
            this._super.apply(this, arguments);
            this.parent = parent;
            this.is_page = is_page;
            this.page = 1;
            this.total_pages = 1;
            this.show_available_products = true;
            this.show_unavailable_products = true;
        },
        willStart: function(){
            var self = this;
            self.trigger_up("loading", {loading: true});
            var user = JSON.parse(Cookies.get("user"));
            let values = {
                token: user.token,
                page: self.page,
            }
            return $.when(this._super.apply(this, arguments),
            ajax.jsonRpc('/barcode_scanner/get/products', 'call', values ))
            .done((args1, args2) => {
                if(args2.hasOwnProperty('result')){
                    self.products = args2.result.products;
                    self.products_to_display = args2.result.products;
                    self.total_pages = args2.result.total_pages;
                }else if(args2.hasOwnProperty("error")){
                    self.trigger_up('checkIfTokenExpired', {value: args2});
                }
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
        _get_products_and_rerender: function(){
            var self = this;
            self.trigger_up("loading", {loading: true});
            let values = {
                token: self.parent.user.token,
                page: self.page, 
                search_text: self.search_text,
                show_available: self.show_available_products,
                show_unavailable: self.show_unavailable_products,
            }
            
            ajax.jsonRpc('/barcode_scanner/get/products', 'call', values)
                .then((data) => {
                    console.log(data)
                    if(data.hasOwnProperty("error")){
                        self.trigger_up('checkIfTokenExpired', {value: data});
                    }
                    self.products = data.result.products;
                    self.products_to_display = data.result.products;
                    self.total_pages = data.result.total_pages;
                    self._rerender();
                    self.trigger_up("loading", {loading: false});
                });
        },
        _search_button_handler: function(){
            var self = this;
            self.search_text = $("#product_search_input").val();
            self._get_products_and_rerender();
            self._rerender();
            $("#product_search_input").focus().val('').val(self.search_text);
        },
        _rerender: function () {
            this.replaceElement(qweb.render('barcode_scanner.product_list', {widget: this}));
        },
    })

    return ProductList;
})