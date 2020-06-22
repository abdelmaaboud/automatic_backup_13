odoo.define('barcode_scanner.Home', function(require){

    var ajax = require("web.ajax");
    var core = require("web.core");
    var router = require('barcode_scanner.router');
    var Widget = require("web.Widget");
    var VideoScanner = require("barcode_scanner.VideoScanner");
    var _t = core._t;
    var Scanner = require("barcode_scanner.Scanner");

    var Home = Widget.extend({
        template:"barcode_scanner.home",
        xmlDependencies: ['/barcode_scanner/static/src/xml/home_view.xml', 
        '/barcode_scanner/static/src/xml/video_scanner.xml'],
        events: {
            'click #tap_to_scan_button' : function(ev){
                this.video_scanner.scan_barcode().then(barcode => {
                    this._barcodeHandler(barcode);
                })
            },
            'click #partners_button': function(ev){
                router.navigate("/partners");
            },
            'click #products_button': function(ev){
                router.navigate("/products");
            },
            'click #inventory_button': function(ev){
                router.navigate("/inventory");
            }
        },
        custom_events: {
            scannedBarcode: '_onScannedBarcode' // This event is called when the scanner object trigger 'scannedBarcode' event
        },
        init: function(parent){
            this._super.apply(this, arguments);
            this.video_scanner = new VideoScanner();
            this.user = JSON.parse(Cookies.get("user"));
            this.scanner = new Scanner(this);
        },
        start: function(){
            var self = this;
            this.trigger_up('loading', {loading: true});
            return this._super.apply(this, arguments).then(function(){
                self.trigger_up('loading', {loading: false});
                self.scanner.appendTo($(".barcode_scanner_app"));
                self.scanner.listen();
            })
        },
        destroy: function(){
            var self = this;
            return $.when(this._super.apply(this, arguments)).then(function(){
                self.scanner.destroy();
                $(this).empty();
            });
        },
        _onScannedBarcode: function(event){
            this.trigger_up("scannerIsListening", {value: false});
            this._barcodeHandler(event.data.value);
        },
        _barcodeHandler: function(barcode){
            this.trigger_up("loading", {loading: true});
            // Check if a product contain this barcode
            ajax.jsonRpc('/barcode_scanner/get/product/', 'call', {product_key: barcode, operation_type_name: "incomming", token: this.user.token})
            .then((data) => {
                if(data.hasOwnProperty("result")){
                    // A product contains this barcode
                    router.navigate("/product/" + barcode);
                    this.trigger_up("loading", {loading: false});
                    this.trigger_up("scannerIsListening", {value: true});
                }else if(data.hasOwnProperty("error")){
                    this.trigger_up("checkIfTokenExpired", {value: data});
                    // Not a single product contains this barcode
                    // Check if a location contains this barcode
                    ajax.jsonRpc('/barcode_scanner/get/location/', 'call', {location_key: barcode, token: this.user.token})
                    .then((data) => {
                        this.trigger_up("loading", {loading: false});
                        this.trigger_up("scannerIsListening", {value: true});
                        if(data.hasOwnProperty("result")){
                            // A location contains this barcode
                            router.navigate("/location/" + barcode);
                        }else if(data.hasOwnProperty("error")){
                            this.trigger_up("checkIfTokenExpired", {value: data});
                            // Not a single location contains this barcode
                            this.trigger_up("warning", {msg: _t("Nothing was found for this barcode")})
                        }
                    })
                }
                this.trigger_up("scannerIsListening", {value: true});
            })
        }
    })

    return Home;

})