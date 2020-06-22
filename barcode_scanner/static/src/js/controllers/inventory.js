odoo.define('barcode_scanner.Inventory', function(require){
    var Widget = require("web.Widget");
    var ajax = require("web.ajax");
    var core = require('web.core');
    var router = require('barcode_scanner.router');
    var ConfirmModal = require("barcode_scanner.ConfirmModal");
    var Scanner = require("barcode_scanner.Scanner");

    var qweb = core.qweb;
    var _t = core._t;

    var VideoScanner = require("barcode_scanner.VideoScanner");

    var Inventory = Widget.extend({
        template: "barcode_scanner.inventory",
        xmlDependencies: ['/barcode_scanner/static/src/xml/inventory_view.xml', 
                            '/barcode_scanner/static/src/xml/video_scanner.xml'],
        events: {
            'click #tap_to_scan_fab' : function(ev){
                ev.preventDefault();
                this._start_video_scanner();
            },
            'change #location': function(ev){
                this._getLocationProducts(ev.currentTarget.value);
                this.location_id = ev.currentTarget.value;
            },
            'click #confirm_button': function(ev){
                this.confirm_modal.ask_confirmation()
                .then(result => {
                    if(result === true){
                        this._confirm_inventory();
                    }
                });
            },
            'click #tap_to_scan_fab': function(ev){
                var video_scanner = new VideoScanner();
                video_scanner.scan_barcode().then(barcode => {
                    this._barcode_handler(barcode);
                });
            },
            'click #home_breadcrumb': function(ev){
                router.navigate("/home");
            }
        },
        custom_events: {
            scannedBarcode: '_onScannedBarcode'
        },
        /* Lifecycle */
        init: function(parent){
            this._super.apply(this, arguments);
            this.parent = parent;
            this.location_id = null;
            this.products = [];
            this.user = JSON.parse(Cookies.get("user"));
            this.scanner = new Scanner(this);
            this.scanner.appendTo($(".barcode_scanner_app"));
            //Confirmation modal init
            this.confirm_modal = new ConfirmModal(this);
            this.confirm_modal.appendTo($(".barcode_scanner_app"));
        },
        willStart: function(){
            var self = this;
            self.trigger_up("loading", {loading: true});
            return $.when(this._super.apply(this, arguments), ajax.jsonRpc('/barcode_scanner/get/locations/', 'call', {token: this.user.token}))
            .done((args1, args2) => {
                if(args2.hasOwnProperty("error")){
                    self.trigger_up('checkIfTokenExpired', {value: args2});
                }else{
                    self.locations = args2.result.locations;
                }
            });
        },
        start: function(){
            var self = this;
            return $.when(this._super.apply(this, arguments)).then(() => {
                self.scanner.listen();
                self.trigger_up('change #location');
                self.location_id = $("#location").val();
                self._set_input_handlers();
                self._init_spinner_handler();
                self.trigger_up("loading", {loading: false});
            });

        },
        destroy: function(){
            var self = this;
            return $.when(this._super.apply(this, arguments)).then(function(){
                $(this).empty();
                self.scanner.destroy();
                document.onkeydown = null;
                $(document).off("click", '.number-spinner button');
            });
        },
        _onScannedBarcode: function(event){
            this.trigger_up("scannerIsListening", {value: false});
            this._barcode_handler(event.data.value).then(()=>{
                this.trigger_up("scannerIsListening", {value: true});
            });
        },
        _confirm_inventory: function(){
            var self = this;
            var product_ids_and_quant = [];
            self.products.forEach((product, index) => {
                let input_id = "#input_" + product.product_id;
                let value = $(input_id).val();
                product_ids_and_quant.push({
                    'id': product.product_id,
                    'qty': value
                })
            })
            ajax.jsonRpc("/barcode_scanner/post/inventory/", 'call',{product_ids_and_quant: product_ids_and_quant, location_key: self.location_id, token: this.user.token})
            .then((data)=>{
                if(data.hasOwnProperty("error")){
                    self.trigger_up('checkIfTokenExpired', {value: data});
                    self.trigger_up("warning", {msg: _t(data.error.message)})
                }else if(data.hasOwnProperty("result")){
                    self._rerender();
                    self.trigger_up("notify", {msg: _t("Inventory completed for this location")})
                    self._rerender();
                }
            })
        }, 
        _getLocationProducts: function(location_id){
            var self = this;
            self.trigger_up("loading", {loading: true});
            ajax.jsonRpc('/barcode_scanner/get/location/', 'call', {'location_key': location_id, token: this.user.token}).then((data)=>{
                if(data.hasOwnProperty("result")){
                    self.products = data.result.products;
                    self.products.forEach((product, index) => {
                        self.products[index] = {...product, selected: 0}
                    })
                    self._rerender();
                }else if(data.hasOwnProperty("error")){
                    self.trigger_up('checkIfTokenExpired', {value: data});
                    self.trigger_up("warning", {msg: _t(data.error.message)})
                }
                self.trigger_up("loading", {loading: false});
            })
        },
        _init_spinner_handler: function(){
            var self = this;
            $(document).on('click', '.number-spinner button', function () {    
                var btn = $(this),
                    oldValue = btn.closest('.number-spinner').find('input').val().trim(),
                    newVal = 0;
                
                if (btn.attr('data-dir') == 'up') {
                    newVal = parseInt(oldValue) + 1;
                } else {
                    newVal = parseInt(oldValue) - 1;
                }
                btn.closest('.number-spinner').find('input').val(newVal).trigger("change");
            });
        },
        _barcode_handler: function(barcode){
            var self = this;
            var barcodeIsHandled = $.Deferred();
            self.parent.trigger_up('loading', {loading: true} )
            this._get_product_info_in_json(barcode).then((data)=>{
                if(data.hasOwnProperty("result")){
                    self._add_to_product_list(data.result);
                    self.parent.trigger_up('loading', {loading: false} )
                }else if(data.hasOwnProperty("error")){
                    self.trigger_up('checkIfTokenExpired', {value: data});
                    self.parent.trigger_up('loading', {loading: false} )
                    self.parent.trigger_up('warning', {title: data.error.message} )
                }
                barcodeIsHandled.resolve(true);
            })
            return barcodeIsHandled.promise();
        },
        _add_to_product_list: function(product){
            var self = this;
            let product_already_added = false;
            for(let i = 0; i < this.products.length; i++){
                if(this.products[i].product_id === product.id){
                    this.products[i].selected = parseInt(this.products[i].selected) + 1;
                    product_already_added = true;
                    break;
                }
            }
            if(!product_already_added){
                this.products.push({
                    'product_id': product.id,
                    'name': product.name,
                    'ref': product.ref,
                    'barcode': product.barcode,
                    'quantity': 0,
                    'selected': 1
                })
            }
            self._rerender();
        },
        _get_product_info_in_json: function(product_key){
            return ajax.jsonRpc('/barcode_scanner/get/product', 'call', {product_key: product_key, operation_type_name:"in", token: this.user.token});
        },
        _set_input_handlers: function(){
            var self = this;
            // Handlers for each product input
            self.products.forEach((product, index) => {
                let input_id = "#input_" + product.product_id;
                $(input_id).attr({
                    min: 0
                });
                $(input_id).change(function(){
                    var min = parseInt($(this).attr('min'));
                    if ($(this).val() < min){
                        $(this).val(min);
                    }
                    self.products[index] = {...product, selected: $(this).val()}
                })
                $(input_id).val(product.selected);
            });
        },

        _rerender: function () {
            this.replaceElement(qweb.render('barcode_scanner.inventory', {widget: this}));
            $("#location").val(this.location_id);
            this._set_input_handlers();
        },
    })

    return Inventory;
})