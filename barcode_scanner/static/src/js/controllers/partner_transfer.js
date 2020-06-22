odoo.define('barcode_scanner.PartnerTransfer', function(require){
    var ajax = require("web.ajax");
    var core = require("web.core");
    var router = require('barcode_scanner.router');
    var ConfirmModal = require("barcode_scanner.ConfirmModal");
    var Widget = require("web.Widget");
    var VideoScanner = require("barcode_scanner.VideoScanner");
    var ProductList = require("barcode_scanner.ProductList");
    var Scanner = require("barcode_scanner.Scanner");
    var qweb = core.qweb;
    var _t = core._t;

    var PartnerSell  = Widget.extend({
        template:"barcode_scanner.partner_transfer",
        xmlDependencies: ['/barcode_scanner/static/src/xml/partner_transfer_view.xml', 
        '/barcode_scanner/static/src/xml/product_list_view.xml', '/barcode_scanner/static/src/xml/video_scanner.xml'],
        events: {
            'click #add_product_button': function(ev){
                ev.preventDefault();
                this._handler_for_add_product_button();
            },
            'click #confirm_button': function(ev){
                this.confirm_modal.ask_confirmation().then(data => {
                    if(data === true){
                        this._handler_for_confirm_button();
                    }
                })
            },
            'click #tap_to_scan_fab' : function(ev){
                ev.preventDefault();
                this._handler_for_floating_action_button();
            },
            'click #home_breadcrumb': function(ev){
                router.navigate("/home");
            },
            'click #partners_breadcrumb': function(ev){
                router.navigate("/partners");
            },
            'click #partner_breadcrumb': function(ev){
                router.navigate("/partner/" + this.partner_key);
            },
            'click .remove-product': function(ev){
                this._remove_product(ev);
            }
        },
        custom_events:{
            scannedBarcode: '_onScannedBarcode'
        },
        /* Lifecycle */
        init: function(parent, partner_key){
            this._super.apply(this, arguments);
            var self = this;
            this.parent = parent;
            this.partner_key = partner_key;
            this.user = JSON.parse(Cookies.get("user"));
            this.products = [];
            this.scanner = new Scanner(this);
            ProductList = ProductList.extend({
                events: _.extend({}, ProductList.prototype.events, {
                    'click .thumbnail': function(ev){
                        var product_key = null;
                        if($(ev.currentTarget).data("name") != "")
                            product_key = $(ev.currentTarget).data("name");
                        else if($(ev.currentTarget).data("barcode") != "")
                            product_key = $(ev.currentTarget).data("barcode");
                        else if($(ev.currentTarget).data("id") != "")
                            product_key = $(ev.currentTarget).data("id")
                        self._handler_for_thumbnail_click(product_key);
                    }
                })
            })
            this.ProductListSelect = new ProductList(self, false);
            //Confirmation modal init
            this.confirm_modal = new ConfirmModal(this);
        },
        willStart: function(){
            var self = this;
            self.trigger_up("loading", {loading: true});
            return $.when(this._super.apply(this, arguments),
            ajax.jsonRpc('/barcode_scanner/get/partner/', 'call', {partner_key: self.partner_key, token: self.parent.user.token}) )
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
                self.confirm_modal.appendTo($(".barcode_scanner_app"));
                self.ProductListSelect.appendTo($("#modal-body"));
                self.scanner.appendTo($(".barcode_scanner_app"));
                self.scanner.listen();
                self._init_select_handlers();
                self.trigger_up("loading", {loading: false});
            });
        },
        destroy: function(){
            var self = this;
            return $.when(this._super.apply(this, arguments)).then(function(){
                $('.modal').remove();
                $('.modal-backdrop').remove();
                $(this).empty();
                document.onkeydown = null;
                self.ProductListSelect.destroy();
                self.confirm_modal.destroy();
                self.scanner.destroy();
                $(document).off("click", '.number-spinner button');
            });
        },
        
        // Handlers
        _remove_product: function(ev){
            var self = this;
            var product_id = ev.currentTarget.getAttribute('data-product-id');
            this.products.forEach((product, index) => {
                if(product.id == product_id){
                    this.products.splice(index, 1);
                }
                self._rerender();
            })
        },
        _handler_for_add_product_button: function(){
            $("#modal").modal('show');
        },
        _handler_for_thumbnail_click: function(product_key){
            var self = this;
            self.parent.trigger_up('loading', {loading: true} )
            this._get_product_info_in_json(product_key).then((data)=>{
                if(data.hasOwnProperty("result")){
                    self._add_to_product_list(data.result);
                    self.parent.trigger_up('loading', {loading: false} )
                }else if(data.hasOwnProperty("error")){
                    self.trigger_up('checkIfTokenExpired', {value: data});
                    self.parent.trigger_up('loading', {loading: false} )
                    self.parent.trigger_up('warning', {title: data.error.message} )
                    self.scannerListener = true;
                }
            })
        },
        _handler_for_confirm_button: function(){
            var self = this;
            ajax.jsonRpc("/barcode_scanner/post/partner/transfer", 'call', {user_id: this.user.id, partner_key: this.partner_key, products: this.products, token: self.parent.user.token})
            .then((data)=>{
                if(data.hasOwnProperty("result")){
                    self.parent.trigger_up("notify", {msg: _t("Transfer validated")});
                    self.print_delivery_slip(data.result.id, data.result.name);
                    router.navigate();
                }else if(data.hasOwnProperty("error")){
                    self.trigger_up('checkIfTokenExpired', {value: data});
                    self.parent.trigger_up("warning", {msg: data.error.message});
                }
            })
        },
        _handler_for_floating_action_button: function(){
            var video_scanner = new VideoScanner();
            video_scanner.scan_barcode().then(barcode => {
                this._handler_for_scanned_barcode(barcode);
            })
        },
        _handler_for_scanned_barcode(barcode){
            this._handler_for_thumbnail_click(barcode);
        },
        _onScannedBarcode: function(event){
            this._handler_for_scanned_barcode(event.data.value);
        },

        // Private methods
        _get_product_info_in_json: function(product_key){
            var user = JSON.parse(Cookies.get("user"));
            return ajax.jsonRpc('/barcode_scanner/get/product', 'call', {product_key: product_key, operation_type_name:"in", token: user.token} );
        },
        _add_to_product_list: function(product){
            var self = this;
            if(product.qty_available <= 0 || product.qty_available - product.reserved_quantity <= 0){
                self.parent.trigger_up("warning", {title:"Product not available !", msg:"There is no quantity available for this product."})
                self.scannerListener = true;
                return;
            }
            let product_already_added = false;
            for(let i = 0; i < this.products.length; i++){
                if(this.products[i].id === product.id){
                    product_already_added = true;
                    this.products[i].quants[0] = {...this.products[i].quants[0], selected: parseInt(this.products[i].quants[0].selected) + 1}
                }
            }
            if(!product_already_added){
                product.quants.forEach((quant, index) => {
                    if(quant.quantity_available - quant.reserved_quantity <= 0){ // To remove ?
                        product.quants.splice(index, 1);
                    }else{
                        product.quants[index] = {...quant, selected: 0};
                    }
                });
                if(product.quants.length === 1){
                    product.quants[0].selected = 1;
                }
                this.products.push(product);
            }
            if(($("#modal").data('bs.modal') || {}).isShown){
                $('#modal').modal('hide');
                $("#modal").on('hidden.bs.modal', function (event) {
                    self._rerender();
                });
            }else{
                self._rerender();
                self.scannerListener = true;
            }
        },

        _init_select_handlers: function(){
            $(document).off("click", '.number-spinner button');
            this._init_input_handler();
            this._init_spinner_handler();
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
        print_delivery_slip: function(picking_id, picking_name){
            this.trigger_up("notify", {msg: _t("Downloading delivery slip")});
            var link = document.createElement('a');
            link.href = "/barcode_scanner/print/picking/delivery/" + picking_id;
            link.download = 'delivery_slip-' + picking_name + ".pdf";
            link.dispatchEvent(new MouseEvent('click'));
        },
        _init_input_handler: function(){
            var self = this;

            this.products.forEach((product,product_index) => {
                product.quants.forEach((quant, quant_index) => {
                    let input_id = "#quant_" + quant.id;
                    $(input_id).attr({
                        max: parseInt(quant.quantity_available - quant.reserved_quantity),
                        min: 0
                    });
                    $(input_id).change(function(){
                        var max = parseInt($(this).attr('max'));
                        var min = parseInt($(this).attr('min'));
                        if ($(this).val() > max){
                            $(this).val(max);
                        }else if ($(this).val() < min){
                            $(this).val(min);
                        }
                        self.products[product_index].quants[quant_index] = {...quant, selected: $(this).val()}
                    })
                    $(input_id).val(quant.selected);
                })
            })
        },

        // Rerender
        _rerender: function () {
            this.replaceElement(qweb.render('barcode_scanner.partner_transfer', {widget: this}));
            this.ProductListSelect.appendTo($("#modal-body"));
            this._init_select_handlers();
        },

    });

    return PartnerSell;

})