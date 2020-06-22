odoo.define('barcode_scanner.Product', function (require){
    'use strict';

    var ajax = require("web.ajax");
    var Widget = require('web.Widget');
    var core = require('web.core');
    var qweb = core.qweb;
    var _t = core._t;

    var router = require("barcode_scanner.router");

    var Product = Widget.extend({
        template:"barcode_scanner.product_info",
        xmlDependencies: ['/barcode_scanner/static/src/xml/product_view.xml'],
        events: {
            'click #incomming_button' : function(ev){
                ev.preventDefault();
                this._incomming();
            },
            "click #edit_button" : function(ev){
                ev.preventDefault();
                if(this.edit_mode === false)
                    this._edit_mode();
                else
                    this._save_product();
            },
            "click #home_breadcrumb": function(ev){
                router.navigate("/home");
            },
            "click #products_breadcrumb": function(ev){
                router.navigate("/products");
            },
            "change #file": function(ev){
                var self = this;
                let file = document.getElementById("file");
                if(file.files[0] != null){
                    self._image_to_binary(file.files[0]).then((image_in_binary) => {
                        $("#product_image").attr(
                            'src', 'data:image/png;base64,' + image_in_binary
                        )
                    });
                }
            },
            'click #discard_edit_button': function(ev){
                var self = this;
                self.edit_mode = false;
                self._rerender();
            }
        },
        /* Lifecycle */
        init: function(parent, product_key){
            this._super.apply(this, arguments);
            this.in_selected = localStorage.getItem("in_selected");
            this.parent = parent;
            this.product_key = product_key;
            this.edit_mode = false;
            localStorage.setItem("incomming", ''); // TODO : Normalement je devrais pas mettre ça
        },
        willStart: function(){
            var self = this;
            self.trigger_up("loading", {loading: true});
            return $.when(this._super.apply(this, arguments),
            ajax.jsonRpc('/barcode_scanner/get/product', 'call', {product_key: self.product_key, operation_type_name: 'in', token: self.parent.user.token}))
            .done((args1, args2) => {
                if(args2.hasOwnProperty("error")){
                    router.navigate();
                    self.parent.trigger_up("warning", {title: "Product not found"});
                    self.trigger_up('checkIfTokenExpired', {value: args2});
                }
                self.product = args2.result;
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
        /* Private methods */
        _incomming: function(){
            var self = this;
            let incomming = localStorage.getItem("incomming");
            if(incomming != null && incomming.product_key == null){
                incomming = {
                    ...incomming, product_key: self.product_key
                }
            }
            localStorage.setItem("incomming", JSON.stringify(incomming));
            router.navigate("/product/" + this.product_key + '/incomming/step/1')
        },
        _edit_mode: function(){
            this.edit_mode = true;
            this._rerender();
            if(this.product.name != false)
                $("#product_name_input").val(this.product.name);
            if(this.product.description != false)
                $("#product_description_input").val(this.product.description);
            if(this.product.ref != false)
                $("#product_ref_input").val(this.product.ref);
            if(this.product.barcode != false)
                $("#product_barcode_input").val(this.product.barcode);
            $("#edit_button").text("Save");
        },
        _image_to_binary:function(file){
            var result = $.Deferred();
            var reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = function () {
                var str = reader.result;
                str = str.slice(str.lastIndexOf(',') + 1);
                result.resolve(str);
            };
            return result.promise();
        },
        _save_product: function(){
            var self = this;
            self.trigger_up("loading", {loading:true});
            self.edit_mode = false;
            self.product.name = $("#product_name_input").val();
            self.product.ref = $("#product_ref_input").val();
            self.product.barcode = $("#product_barcode_input").val();
            self.product.description = $("#product_description_input").val();
            
            let file = document.getElementById("file");
            if(file.files[0] != null){
                self._image_to_binary(file.files[0]).then((image_in_binary) => {
                    self.product.image = image_in_binary;
                    self._save_product_rpc();
                });
            }else{
                self._save_product_rpc();
            }
        },
        _save_product_rpc: function(){
            var self = this;
            var product_key_changed = true;
            ajax.jsonRpc("/barcode_scanner/put/product/", 'call', {product: self.product, token: self.parent.user.token}).then(function(data){
                if(data.hasOwnProperty("error")){
                    self.trigger_up("warning", {msg: _t(data.error.message)})
                }else{
                    for(var propertyName in self.product) {
                        if(self.product[propertyName] === self.product_key){
                            product_key_changed = false;
                            break;
                        }
                    }
                    if(product_key_changed)
                        router.navigate('/product/' + self.product.name);
                    else
                        self._rerender();
                }
                self.trigger_up("loading", {loading:false});
            });
        },
        _rerender: function () {
            this.replaceElement(qweb.render('barcode_scanner.product_info', {widget: this}));
        },
    })

    return Product;
})