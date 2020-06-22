odoo.define("barcode_scanner.PickingList", function(require){

    var Widget = require("web.Widget");
    var router = require("barcode_scanner.router");
    var ajax = require("web.ajax");
    var ConfirmModal = require("barcode_scanner.ConfirmModal");
    var core = require("web.core");
    var qweb = core.qweb;
    var _t = core._t;

    var PickingList = Widget.extend({
        template: 'barcode_scanner.picking_list',
        xmlDependencies: ['/barcode_scanner/static/src/xml/picking_list_view.xml'],
        events: {
            'click .list-group-item': function(ev){
                this._navigateToSelectedPicking($(ev.currentTarget).data("id"));
            },
            'click #home_breadcrumb': function(ev){
                router.navigate("/home");
            },
            'click #partners_breadcrumb': function(ev){
                router.navigate("/partners");
            },
            'click #partner_breadcrumb': function(ev){
                router.navigate("/partner/" + this.model_key);
            },
            'click #finish_incomming_process': function(ev){
                this.confirm_modal.ask_confirmation().then((data)=>{
                    if(data === true){
                        var move_id = this.incomming.in_moves[0].id; // Incomming moves that were validated (there is actually only one move)
                        var to_process = parseInt(this.incomming.in_selected) - parseInt(this.incomming.out_selected); // How much products to process
                        this.print_move_label(move_id, to_process);
                        router.navigate("/home");
                    }
                })

            }
        },
        /* Lifecycle */
        init: function(parent, model_key, operation_type_name, model="product"){
            this._super.apply(this, arguments);
            this.parent = parent;
            this.model_key = model_key;
            this.confirm_modal = new ConfirmModal(this);
            this.operation_type_name = operation_type_name;
            if(model === "product")
                this.incomming = JSON.parse(localStorage.getItem("incomming"));
            this.model = model;
            this.user = JSON.parse(Cookies.get("user"));
        },
        willStart: function(){
            var self = this;
            self.trigger_up("loading", {loading: true});
            let model_key_string = ''+ self.model + '_key';
            return $.when(this._super.apply(this, arguments),
            ajax.jsonRpc('/barcode_scanner/get/' + self.model, 'call', {[model_key_string]: self.model_key, token: self.user.token, operation_type_name: self.operation_type_name, unwanted_states:["done",'cancel']}))
            .done((args1, args2) => {
                if(args2.hasOwnProperty("error")){
                    self.trigger_up('checkIfTokenExpired', {value: args2});
                    self.trigger_up("notify", {msg: _t(args2.error.message)})
                }else if(args2.hasOwnProperty("result")){
                    self.product = args2.result;
                    // Redirect if there is no pickings for this product.
                    if(self.product.pickings.length === 0 && self.operation_type_name === "in"){
                        router.navigate("/"+ self.model + "/" + self.model_key);
                    }
                }
                self.trigger_up("loading", {loading: false});
            });
        },
        start: function(){
            var self = this;
            return $.when(this._super.apply(this, arguments)).then(()=>{
                this.confirm_modal.appendTo($(".barcode_scanner_app"));
            });
        },
        destroy: function(){
            return $.when(this._super.apply(this, arguments)).then(function(){
                if(this.confirm_modal != null)
                    this.confirm_modal.destroy();
                $(this).empty();
            });
        },
        _navigateToSelectedPicking: function(picking_id){
            var self = this;
            if(self.operation_type_name === "in"){
                let incomming = JSON.parse(localStorage.getItem("incomming"));
                incomming = {
                    ...incomming, picking_in_id: picking_id
                }
                localStorage.setItem("incomming", JSON.stringify(incomming));
                router.navigate( self.model + '/' + self.model_key + "/incomming/step/2");
            }
            else if(self.operation_type_name === "out"){
                let incomming = JSON.parse(localStorage.getItem("incomming"));
                incomming = {
                    ...incomming, picking_out_id: picking_id
                }
                localStorage.setItem("incomming", JSON.stringify(incomming));
                router.navigate( self.model + '/' + self.model_key + "/incomming/step/4");
            }
        },
        download_move_label: function(id){ // Give an id
            var link = document.createElement('a');
            link.href = "/barcode_scanner/report/move/label/" + id;
            link.download = 'file.pdf';
            link.dispatchEvent(new MouseEvent('click'));
        },
        print_move_label: function(id, quantity){
            var self = this;
             return ajax.jsonRpc("/barcode_scanner/print/move/label", 'call', {move_id: id, quantity:quantity}).then(data=>{
                if(data.hasOwnProperty("error")){
                    self.trigger_up("warning", {msg:data.error.message});
                }else if(data.hasOwnProperty("result")){
                    self.trigger_up("notify", {msg: _t("Printing tickets")})
                }
             });
        },

    })
    return PickingList;
});