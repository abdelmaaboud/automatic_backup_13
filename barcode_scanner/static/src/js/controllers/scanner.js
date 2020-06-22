odoo.define("barcode_scanner.Scanner", function(require){

    var Widget = require("web.Widget");

    var Scanner = Widget.extend({
        template: "barcode_scanner.scanner",
        xmlDependencies: ["/barcode_scanner/static/src/xml/scanner_view.xml"],
        custom_events: {
            scannerIsListening: '_isListening'
        },
        init: function(parent){
            this._super.apply(this, arguments);
            this.isListening = true;
        },
        destroy: function(){
            return $.when(this._super.apply(this, arguments)).then(()=>{
                document.onkeydown = null;
            })
        },
        /* Will create an event onkeydown and listen to any scanned code. Then it will trigger scannedBarcode event */
        listen: function(){
            var self = this;
            document.onkeydown = function(e) {
                if(self.isListening === true){
                    var code = (e.keyCode ? e.keyCode : e.which);
                    if((code==13 || code==9) && $("#barcode_input").val() != ""){ // 13 = Enter key hit, 9 = Tab key hit
                        var barcode = $("#barcode_input").val();
                        if(barcode != ''){
                            window.navigator.vibrate(100);
                            self.trigger_up("scannedBarcode", {value: barcode});
                            $("#barcode_input").val('');
                            $("#barcode_input").blur();
                        }
                    }else if(code == 0 && self.isListening === true ){
                        /* The 0 keycode is used by Zebra when we use the integrated scanner */
                        $("#barcode_input").focus();
                        setTimeout(function(){ // After 1s, automatically unfocus the input
                            $("#barcode_input").blur();
                        }, 1000);
                    }
                }
            }
        },
        isListening: function(event){
            if(event.data.value === true){
                this.isListening = true;
            }else if(event.data.value === false){
                this.isListening = false;
            }
        }
    })

    return Scanner;
})