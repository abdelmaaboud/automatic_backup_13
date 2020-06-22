odoo.define('barcode_scanner.Picking', function (require){
    'use strict';

    var core = require('web.core');
    var ajax = require('web.ajax');
    var Widget = require('web.Widget');
    var ConfirmModal = require("barcode_scanner.ConfirmModal");
    var qweb = core.qweb;
    var _t = core._t;
    var router = require('barcode_scanner.router');
    var VideoScanner = require("barcode_scanner.VideoScanner");
    var Scanner = require("barcode_scanner.Scanner");

    var Picking = Widget.extend({
        template:"barcode_scanner.picking_info",
        xmlDependencies: ['/barcode_scanner/static/src/xml/picking_view.xml', 
        '/barcode_scanner/static/src/xml/video_scanner.xml'],
        events: {
            'click #validate_picking_button': function(ev){ // Continue button, used by the two types of picking (in and out)
                this.confirm_modal.ask_confirmation().then(data => {
                    if(data === true){
                        if(this.operation_type_name === 'in')
                            this._validateIncommingPicking(); // If the picking is an incomming 
                        else if(this.operation_type_name === 'out')
                            this._validateOutgoingPicking(); // If the picking is an outgoing
                    }
                });
            },
            'click #tap_to_scan_fab' : function(ev){
                this.video_scanner.scan_barcode().then(barcode => {
                    this._scanned_barcode_handler(barcode); // When the camera scan a barcode, we call the barcode handler method
                })
            },
            'click #finish_incomming_picking_button': function(ev){ // This button exists only for incomming types of picking
                this.confirm_modal.ask_confirmation().then(data => {
                    if(data === true){
                        this.process_finished = true;
                        this._validateIncommingPicking();
                    }
                });
            }
        },
        custom_events:{
            scannedBarcode: '_onScannedBarcode'
        },
        init: function(parent, product_key, picking_key, operation_type_name){
            this._super.apply(this, arguments);
            this.parent = parent;
            this.video_scanner = new VideoScanner();
            this.operation_type_name = operation_type_name;
            this.product_key = product_key; // Can be the barcode, the ref or the name of the product
            this.picking_key = picking_key; // Can be the barcode, the ref or the name of the picking
            this.incomming = JSON.parse(localStorage.getItem("incomming"));
            this.process_finished = false;
            this.outgoing_exists = false;
            this.user = JSON.parse(Cookies.get("user"));
            this.picking = null;
            this.confirm_modal = new ConfirmModal(this);
            this.scanner = new Scanner(this);
            if(this.incomming.out_selected == null){
                this.incomming= {
                    ...this.incomming, out_selected: 0
                }
            }
        },
        willStart: function(){
            var self = this;
            this.trigger_up("loading", {loading: true});
            return $.when(this._super.apply(this, arguments),
                        ajax.jsonRpc('/barcode_scanner/get/product/picking', 'call', { product_key: self.product_key, picking_key: self.picking_key,token: self.user.token }),
                        ajax.jsonRpc('/barcode_scanner/get/product', 'call', {token: self.user.token, product_key: self.product_key, operation_type_name: "out"}) )
            .done((args1, args2, args3) => { // args2 => one specific picking (this.picking_key) for one product (this.product_key) - args3 => one specific product (this.product_key)
                if(args2.hasOwnProperty("result")){
                    self.picking = args2.result;
                    self.picking.moves.forEach((move, index) => {
                        let selected = 0;
                        if(move.product_id == self.picking.product.id){
                            selected++;
                        }
                        self.picking.moves[index] = {...move, selected: selected}
                    });
                }else if(args2.hasOwnProperty("error")){
                    self.trigger_up('checkIfTokenExpired', {value: args2});
                    router.navigate('/home');
                    self.parent.trigger_up("warning", {msg: args2.error.message})
                }
                if(args3.hasOwnProperty("result")){
                    if(args3.result.pickings.length > 0)
                        self.outgoing_exists = true;
                }
            })
        },
        start: function(){
            return $.when(this._super.apply(this, arguments))
            .then(() => {
                if(this.picking != undefined){
                    this._setHandlersForEachInputOfProducts(); // We set the handler for all inputs
                    this._init_spinner_handler(); // We set the two button used as a spinner number
                }
                // We append the confirmation modal to the DOM
                this.confirm_modal.appendTo($(".barcode_scanner_app"));
                // We append the scanner to the DOM and we listen to all the scanned barcode
                this.scanner.appendTo($(".barcode_scanner_app"));
                this.scanner.listen();
                this.trigger_up("loading",{loading: false});
            })
        },
        destroy: function(){
            return $.when(this._super.apply(this, arguments)).then(function(){
                if(this.confirm_modal != null)
                    this.confirm_modal.destroy();
                if(this.scanner != null)
                    this.scanner.destroy();
                $(this).empty();
                $(document).off("click", '.number-spinner button');
            })
        },
        _validateOutgoingPicking: function(){
            var self = this;
            this.trigger_up("loading", {loading: true});
            let moves = []; // Moves that will be sent to the controller for processing
            let out_selected = 0; // Quantity selected for the reservation
            self.picking.moves.forEach((move, index) => {
                if(move.selected > 0){
                    moves.push(move);
                    out_selected += move.selected;
                }
            });
            let incomming = JSON.parse(localStorage.getItem("incomming")); // Represent all the incomming process
            let previous_out_selected = incomming.out_selected;
            if(previous_out_selected == null){
                previous_out_selected = 0;
            }
            incomming = {
                ...incomming, out_selected: parseInt(previous_out_selected + parseInt(out_selected), 10)
            }
            localStorage.setItem("incomming", JSON.stringify(incomming));
            let user = JSON.parse(Cookies.get("user"));
            ajax.jsonRpc('/barcode_scanner/put/outgoing/validate', 'call', { // We validate the outgoing picking
                user_id: user.id,
                picking_key: self.picking_key,
                product_key: self.product_key,
                moves: moves,
                token: self.user.token
            })
            .then((data) => { // We then check if the product still has some outgoing pickings
                if(data.hasOwnProperty("error")){
                    self.trigger_up('checkIfTokenExpired', {value: data});
                }
                ajax.jsonRpc('/barcode_scanner/get/product', 'call', {product_key: self.product_key, operation_type_name: "out", token: self.user.token} )
                .then((data) => {
                    // If the product still have outgoing pickings and we still have incommings products to process then
                    // we go back to the step 3 where we select the outgoing picking
                    if(incomming.in_selected - incomming.out_selected > 0 && data.result.pickings.length > 0){
                        router.navigate("/product/" + self.product_key + '/incomming/step/3');
                        let selected_to_process = parseInt(incomming.in_selected) - parseInt(incomming.out_selected);
                        self.parent.trigger_up("notify", {msg: "You still have " + selected_to_process + " of " + data.result.name +  " products to process"})
                        self.parent.trigger_up("notify", {msg: "Printing " + out_selected + " OUT Labels for " + data.result.name + " product"})
                        for(let i = 1; i <= out_selected; i++){
                            self.print_move_label(moves[0].id);
                        }
                        self.download_move_label(moves[0].id);
                    }else if(incomming.in_selected - incomming.out_selected > 0 && data.result.pickings.length < 0){
                        // If there is no more products to process, we process all the operations that we did
                        router.navigate("/home/");
                        self.parent.trigger_up("notify", {msg: "Printing " + incomming.in_selected + " IN Labels for " + data.result.name + " products"})
                        for(let i = 1; i <= incomming.in_selected; i++){
                            self.print_move_label(moves[0].id);
                        }
                        self.download_move_label(moves[0].id);
                        self.parent.trigger_up("notify", {msg: "Printing " + out_selected + " OUT Labels for " + data.result.name + " product"})
                        for(let i = 1; i <= out_selected; i++){
                            self.print_move_label(moves[0].id);
                        }
                        self.download_move_label(moves[0].id);
                        localStorage.removeItem("incomming");
                    }else{
                        // If there is no outgoing picking for this product, then we directly process the outgoing picking
                        router.navigate("/home");
                        self.parent.trigger_up("notify", {msg: "Printing " + out_selected + " OUT Labels for " + data.result.name + " product"})
                        for(let i = 1; i <= out_selected; i++){
                            self.print_move_label(moves[0].id);
                        }
                        self.download_move_label(moves[0].id);
                        localStorage.removeItem("incomming");
                    }
                    self.trigger_up("loading", {loading: false});
                })
            })
        },
        _onScannedBarcode: function(ev){
            this._scanned_barcode_handler(ev.data.value);
        },
        _validateIncommingPicking: function(){
            var self = this;
            this.trigger_up("loading", {loading: true});
            let selected = 0;
            let moves = [];
            self.picking.moves.forEach((move, index) => {
                if(move.selected > 0){
                    moves.push(move);
                    selected += move.selected;
                }
            });
            let new_incomming = {
                ...self.incomming, 
                in_selected: parseInt(selected, 10),
                in_moves: self.picking.moves,
                in_validated: true
            }
            localStorage.setItem("incomming", JSON.stringify(new_incomming));
            let user = JSON.parse(Cookies.get("user"));
            let picking_ids_to_validate = JSON.parse(localStorage.getItem("picking_ids_to_validate"));
            if(picking_ids_to_validate == null)
                picking_ids_to_validate = [];
            if(!picking_ids_to_validate.includes(self.picking.id))
                picking_ids_to_validate.push(self.picking.id);
            localStorage.setItem("picking_ids_to_validate", JSON.stringify(picking_ids_to_validate));
            ajax.jsonRpc('/barcode_scanner/put/incomming/validate', 'call', {
                user_id: user.id,
                picking_id:self.picking.id,
                moves: moves,
                token: self.user.token
            })
            .then((data) => {
                if($("#last_incomming_checkbox").is(":checked") && localStorage.getItem("picking_ids_to_validate") != null){
                    ajax.jsonRpc('/barcode_scanner/put/pickings/validate', 'call', {token: self.user.token, picking_ids: JSON.parse(localStorage.getItem("picking_ids_to_validate")) }).then(function(data){
                        localStorage.removeItem("picking_ids_to_validate");
                    });
                }
                if(self.process_finished === true){
                    data.result.moves.forEach(move_id => {
                        console.log("Download")
                        self.print_move_label(move_id, parseInt(selected, 10)).done(() => {
                            router.navigate("/product/")
                        });
                        self.download_move_label(move_id, parseInt(selected, 10));
                    })
                }else{
                    if(self.outgoing_exists)
                        router.navigate("/product/" + self.product_key + '/incomming/step/3');
                    else
                        router.navigate("/home");
                    self.trigger_up('loading', {loading: false});
                }
            })
        },
        _init_spinner_handler: function(){
            // Method that will init all the spinner button for each inputs
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
        _setHandlersForEachInputOfProducts: function(){
            // Method that will set the handler to each input corresponding to each products
            var self = this;
            // Handlers for each product input
            self.picking.moves.forEach((move, index) => {
                let input_id = "#product_" + move.product_id;
                if(self.operation_type_name === "in"){
                    $(input_id).attr({
                        max: parseInt(move.ordered_qty - move.qty_done),
                        min: 1
                    })
                }else if(self.operation_type_name === "out"){
                    $(input_id).attr({
                        max: parseInt(move.ordered_qty - move.reserved),
                        min: 1
                    })
                }
                $(input_id).change(function(){
                    var max = parseInt($(this).attr('max'));
                    var min = parseInt($(this).attr('min'));
                    if ($(this).val() > max){
                        $(this).val(max);
                    }
                    else if ($(this).val() < min){
                        $(this).val(min);
                    }
                    else if ($(this).val() > parseInt(self.incomming.in_selected) - parseInt(self.incomming.out_selected)){
                        $(this).val(parseInt(self.incomming.in_selected) - parseInt(self.incomming.out_selected));
                    }
                    self.picking.moves[index] = {...move, selected: $(this).val()}
                })
                $(input_id).val(move.selected);
            });
        },
        _scanned_barcode_handler: function(barcode){
            window.navigator.vibrate(100);
            var product_input_found = false;
            // Check if a product contain this barcode
            $('input[type=number]').each(function(){
                if($(this).data("barcode") == barcode){
                    let actual_value = $(this).val();
                    $(this).val(++actual_value).trigger('change');
                    product_input_found = true;
                }
            })
            if(!product_input_found){
                this.trigger_up("warning", {msg: "Barcode does not correspond"});
            }
        },
        download_move_label: function(id, quantity){ // Give an id
            //var link = document.createElement('a');
            //link.href = "/barcode_scanner/report/move/label/" + id + "/" + quantity;
            //link.download = 'file.pdf';
            //link.dispatchEvent(new MouseEvent('click'));
            console.log("DOWNLAOD")
        },
        print_move_label: function(id, quantity){
            var self = this;
            self.trigger_up("loading", {loading: true})
             return ajax.jsonRpc("/barcode_scanner/print/move/label", 'call', {move_id: id, quantity:quantity}).then(data=>{
                if(data.hasOwnProperty("error")){
                    self.trigger_up("warning", {msg:data.error.message});
                }else if(data.hasOwnProperty("result")){
                    self.trigger_up("notify", {msg: _t("Printing tickets")})
                }
                 self.trigger_up("loading", {loading: false})
             });
        },

        //Rerender method for picking
        _rerender: function () {
            this.replaceElement(qweb.render('barcode_scanner.app', {widget: this}));
        },
    })

    return Picking;
})