odoo.define("barcode_scanner.IncommingProcess", function(require){
    "user strict";

    var Widget = require("web.Widget");
    var PickingList = require("barcode_scanner.PickingList");
    var Picking = require("barcode_scanner.Picking");

    var router = require("barcode_scanner.router");


    var Incomming = Widget.extend({
        template: 'barcode_scanner.incomming_process',
        xmlDependencies: ['/barcode_scanner/static/src/xml/incomming_process_view.xml'],
        events:{
            'click #home_breadcrumb': function(ev){
                router.navigate("/home");
            },
            'click #products_breadcrumb': function(ev){
                router.navigate("/products");
            },
            'click #product_breadcrumb': function(ev){
                router.navigate("/product/" + this.product_key)
            }
        },
        custom_events:{
            'goToStep': function(ev){
                this._goToStep(ev.data.step);
            }
        },
        /* Lifecycle */
        init: function(parent, product_key, step){
            this._super.apply(this, arguments);
            this.parent = parent;
            this.product_key = product_key;
            this.product_scanned = 0;
            this.widget = null;
            this.step = step;
        },
        willStart: function(){
            this.trigger_up("loading", {loading: true});
            return $.when(this._super.apply(this, arguments));
        },
        start: function(){
            return $.when(this._super.apply(this, arguments)).then(() => {
                this._goToStep(this.step);
                this.trigger_up("loading", {loading: false});
            });

        },
        destroy: function(){
            return $.when(this._super.apply(this, arguments)).then(() => {
                $(this).empty();
            });
        },
        /* End of Lyfecycle */
        _goToStep: function(step){
            if(this.widget != null)
                this.widget.destroy();
            var element = document.getElementById("barcode_scanner.incomming.app");
            var incomming = JSON.parse(localStorage.getItem("incomming"));
            if(incomming == null){
                router.navigate("/home");
                return;
            }
            let stepClass = "step" + step;
            $("."+stepClass).addClass("step-active");
            if(incomming.in_validated != null){
                if(incomming.in_validated === true && step < 3){
                    router.navigate("/product/" + this.product_key + "/incomming/step/3")
                    this.trigger_up("warning", {title: "Finish the process !", msg: "Incomming picking already validated."})
                }
                if(step > 2 && incomming.in_validated === true){
                    for(let i = 0; i <= 2; i++){
                        let stepClass2 = "step" + i;
                        $("."+stepClass2).addClass("step-success");
                    }
                }
            }
            switch (step) {
                case 1:
                    this.widget = new PickingList(this, this.product_key, 'in');
                    this.widget.appendTo(element);
                    break;
                case 2:
                    this.widget = new Picking(this, this.product_key, incomming.picking_in_id, 'in');
                    this.widget.appendTo(element);
                    break;
                case 3:
                    this.widget = new PickingList(this, this.product_key, 'out');
                    this.widget.appendTo(element);
                    break;
                case 4:
                    this.widget = new Picking(this, this.product_key, incomming.picking_out_id, 'out');
                    this.widget.appendTo(element);
                    break;
                default:
                    break;
            }
        }

    })

    return Incomming;
})