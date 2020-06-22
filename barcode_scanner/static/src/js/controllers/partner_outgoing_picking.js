odoo.define('barcode_scanner.PartnerPicking', function (require){
    'use strict';

    var core = require('web.core');
    var ajax = require('web.ajax');
    var Widget = require('web.Widget');
    var ConfirmModal = require("barcode_scanner.ConfirmModal");
    var qweb = core.qweb;
    var _t = core._t;

    var router = require('barcode_scanner.router');

    var PartnerPicking = Widget.extend({
        template:"barcode_scanner.partner_outgoing_picking",
        xmlDependencies: ['/barcode_scanner/static/src/xml/partner_outgoing_picking_view.xml'],
        events: {
            'click #validate_picking_button': function(ev){
                this.confirm_modal.ask_confirmation().then((data)=>{
                    if(data === true){
                        this._validateOutgoingPicking();
                    }
                })
            },
            'click #home_breadcrumb': function(ev){
                router.navigate("/home");
            },
            'click #partners_breadcrumb': function(ev){
                router.navigate("/partners");
            },
            'click #partner_breadcrumb': function(ev){
                router.navigate("/partner/" + this.partner_key)
            }
        },
        init: function(parent, picking_key, partner_key){
            this._super.apply(this, arguments);
            this.parent = parent;
            this.partner_key = partner_key;
            this.picking_key = picking_key; // Can be the barcode, the ref or the name of the picking
            this.user = JSON.parse(Cookies.get("user"));
            this.confirm_modal = new ConfirmModal(this);
        },
        willStart: function(){
            this.trigger_up("loading", {loading: true});
            return $.when(this._super.apply(this, arguments),
                        ajax.jsonRpc('/barcode_scanner/get/partner/picking', 'call', { picking_key: this.picking_key, token: this.user.token }) )
            .done((args1, args2) => {
                if(args2.hasOwnProperty("result")){
                    this.picking = args2.result;
                    this.picking.moves.forEach((move, move_index) => {
                        move.move_lines.forEach((move_line, move_line_index) => {
                            this.picking.moves[move_index].move_lines[move_line_index] = {...move_line, selected: 0}
                        })
                    });
                }else if(args2.hasOwnProperty("error")){
                    this.trigger_up('checkIfTokenExpired', {value: args2});
                }
            })
        },
        start: function(){
            return $.when(this._super.apply(this, arguments)).then(()=>{
                this._init_input_handler();
                this._init_spinner_handler();
                this.confirm_modal.appendTo($(".barcode_scanner_app"));
                this.trigger_up("loading", {loading: false});
            });
        },
        destroy: function(){
            return $.when(this._super.apply(this, arguments)).then(function(){
                $(document).off("click", '.number-spinner button');
                $(this).empty();
            })
        },
        _validateOutgoingPicking: function(){
            ajax.jsonRpc("/barcode_scanner/put/picking/done", 'call', {user_id: this.user.id, picking_key: this.picking_key, moves: this.picking.moves, token: this.user.token} )
            .then((data) => {
                if(data.hasOwnProperty("error")){
                    this.trigger_up('checkIfTokenExpired', {value: data});
                    this.parent.trigger_up("warning", {msg: data.error.message})
                }else if(data.hasOwnProperty("result")){
                    router.navigate("/partner/" + this.partner_key);
                    this.trigger_up("notify", {msg: _t("Outgoing picking validated.")})
                    this.download_delivery_slip();
                }
            })
        },
        download_delivery_slip: function(){
            this.trigger_up("notify", {msg: _t("Downloading delivery slip")})
            var link = document.createElement('a');
            link.href = "/barcode_scanner/print/picking/delivery/" + this.picking.id;
            link.download = 'delivery_slip-' + this.picking.name + ".pdf";
            link.dispatchEvent(new MouseEvent('click'));
        },
        _init_spinner_handler: function(){
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
        _init_input_handler: function(){
            var self = this;
            this.picking.moves.forEach((move,move_index) => {
                move.move_lines.forEach((move_line, move_line_index) => {
                    let input_id = "#move_line_" + move_line.id;
                    $(input_id).attr({
                        max: parseInt(move_line.product_qty),
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
                        self.picking.moves[move_index].move_lines[move_line_index] = {...move_line, selected: $(this).val()}
                    })
                    $(input_id).val(move_line.selected);
                })
            })
        },

        //Rerender method for picking
        _rerender: function () {
            this.replaceElement(qweb.render('barcode_scanner.app', {widget: this}));
        },
    })

    return PartnerPicking;
})