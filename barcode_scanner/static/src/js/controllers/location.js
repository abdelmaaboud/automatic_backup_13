odoo.define('barcode_scanner.Location', function(require){

    var Widget = require("web.Widget");
    var ajax = require("web.ajax");
    var core = require('web.core');
    var router = require('barcode_scanner.router');
    var Scanner = require("barcode_scanner.Scanner");
    var ConfirmModal = require("barcode_scanner.ConfirmModal");

    var qweb = core.qweb;
    var _t = core._t;

    var VideoScanner = require("barcode_scanner.VideoScanner");

    var Location = Widget.extend({
        template: "barcode_scanner.location",
        xmlDependencies: ['/barcode_scanner/static/src/xml/location_view.xml', 
                            '/barcode_scanner/static/src/xml/video_scanner.xml'],
        events: {
            'click #tap_to_scan_fab' : function(ev){
                ev.preventDefault();
                this._handler_for_fab();
            }
        },
        custom_events: {
            scannedBarcode: '_onScannedBarcode'
        },
        init: function(parent, barcode){
            this._super.apply(this, arguments);
            this.parent = parent;
            this.barcode_location = barcode;
            this.video_scanner = new VideoScanner();
            this.scanner = new Scanner(this); 
            this.user = JSON.parse(Cookies.get("user"));
            this.confirm_modal = new ConfirmModal(this);
        },
        willStart: function(){
            var self = this;
            self.trigger_up("loading",{loading: true});
            return $.when(this._super.apply(this, arguments),
                            ajax.jsonRpc('/barcode_scanner/get/location/', 'call', {'location_key': self.barcode_location, token: self.parent.user.token} )
            ).done(function(args1, args2){
                if(args2.hasOwnProperty("error")){
                    router.navigate("/home");
                    self.parent.trigger_up("warning", {msg: _t(args2.error.message)})
                }else if(args2.hasOwnProperty('result')){
                    self.location = args2.result;
                    self.location.products.forEach( (product, index) => {
                        self.location.products[index] = {...product, selected: 0}
                    });
                }
            })
        },
        start: function(){
            var self = this;
            return $.when(this._super.apply(this, arguments)).then(() => {
                self._input_init();
                self.scanner.appendTo($(".barcode_scanner_app"));
                self.scanner.listen();
                self.confirm_modal.appendTo($(".barcode_scanner_app"));
                self.trigger_up("loading", {loading: false});
            });
        },
        destroy: function(){
            var self = this;
            return $.when(this._super.apply(this, arguments)).then(function(){
                self.confirm_modal.destroy();
                self.scanner.destroy();
                $(this).empty();
            });
        },
        _onScannedBarcode: function(event){
            this._barcode_handler(event.data.value);
        },
        _handler_for_fab: function(){
            this.video_scanner.scan_barcode().then(barcode => {
                this._barcode_handler(barcode);
            })
        },
        _input_init: function(){
            var self = this;
            $("#loader").addClass("is-active");
            // Handlers for each product input
            self.location.products.forEach((product, index) => {
                let input_id = "#product_" + product.product_id;
                $(input_id).attr({
                    max: parseInt(product.quantity),
                    min: 0
                })
                $(input_id).change(function(){
                    var max = parseInt($(this).attr('max'));
                    var min = parseInt($(this).attr('min'));
                    if ($(this).val() > max){
                        $(this).val(max);
                    }else if ($(this).val() < min){
                        $(this).val(min);
                    }
                    self.location.products[index] = {...product, selected: $(this).val()}
                })
                $(input_id).val(product.selected);
            });
            $("#loader").removeClass("is-active");
        },
        _increment_product: function(barcode){
            var is_a_product = false;
            $('input[type=number]').each(function(){
                if($(this).data("barcode") == barcode){
                    let actual_value = $(this).val();
                    $(this).val(++actual_value).trigger('change');
                    is_a_product = true;
                }
            })
            return is_a_product;
        },
        _selected_products_ids_and_quants: function(){
            var product_ids_and_selected_quants = [];
            this.location.products.forEach((product) => {
                if(product.selected > 0){
                    let input_id = "#product_" + product.product_id;
                    product_ids_and_selected_quants.push({
                        id: product.product_id,
                        qty: $(input_id).val()
                    })
                }
            });
            return product_ids_and_selected_quants;

        },
        _barcode_handler: function(scanned_barcode){
            var self = this;
            if(!this._increment_product(scanned_barcode)){
                ajax.jsonRpc('/barcode_scanner/get/location/', 'call', {location_key: scanned_barcode, token: self.user.token})
                .then((data) => {
                    if(data.hasOwnProperty("result")){
                        self.confirm_modal.ask_confirmation().then((confirmation)=>{
                            if(confirmation === true){
                                // The scanned barcode correspond to a location
                                let location_id = self.location.location_id;
                                let location_dest_id = data.result.location_id;
                                let product_ids_and_quants = self._selected_products_ids_and_quants();
                                if(product_ids_and_quants.length > 0){
                                    ajax.jsonRpc('/barcode_scanner/post/location/transfer', 'call', {
                                        user_id: self.user.id,
                                        location_id : location_id,
                                        location_dest_id: location_dest_id,
                                        product_ids_and_quants: product_ids_and_quants,
                                        token: self.user.token
                                    })
                                    .then(() => {
                                        router.navigate('/home');
                                        $("#loader").removeClass("is-active");
                                        self.parent.trigger_up("notify",  {msg: _t('Transfer created')} );
                                    })
                                }else{
                                    // Nothing to transfer
                                    $("#loader").removeClass("is-active");
                                    self.parent.trigger_up("warning",  {msg: _t('There is nothing to transfer')} );
                                }
                                this.trigger_up("scannerIsListening", {value: true});
                            }
                        });
                    }else if(data.hasOwnProperty("error")){
                        self.trigger_up('checkIfTokenExpired', {value: data});
                        // Location not found
                        $("#loader").removeClass("is-active");
                        self.parent.trigger_up("warning",  {msg: _t('Not a location nor a product')} );
                        this.trigger_up("scannerIsListening", {value: true});
                    }
                })
            }
        },

        _rerender: function () {
            this.replaceElement(qweb.render('barcode_scanner.location', {widget: this}));
        },
    })

    return Location;

})