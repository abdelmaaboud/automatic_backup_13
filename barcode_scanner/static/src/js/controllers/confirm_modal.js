odoo.define("barcode_scanner.ConfirmModal", function(require){

    var Widget = require("web.Widget");

    var ConfirmModal = Widget.extend({
        template: "barcode_scanner.confirm_modal",
        xmlDependencies: ['/barcode_scanner/static/src/xml/confirm_modal_view.xml'],
        /* Lifecycle */
        init: function(parent){
            this._super.apply(this, arguments);
            this.result = $.Deferred();
        },
        willStart: function(){
            return $.when(this._super.apply(this, arguments));
        },
        start: function(){
            var self = this;
            return $.when(this._super.apply(this, arguments)).then(()=>{
                $("#modal-confirm-button").on('click', function(ev){
                    $("#confirm_modal").modal('hide');
                    self.result.resolve(true);
                });
                $("modal-cancel-button").on("click", function(ev){
                    $("#confirm_modal").modal('hide');
                    self.result.resolve(false);
                });
            });

        },
        destroy: function(){
            return $.when(this._super.apply(this, arguments)).then(function(){
                $(this).empty();
                $('.modal').remove();
                $('.modal-backdrop').remove();
                $('body').removeClass('modal-open');
                $("#modal-confirm-button").on('click', function(ev){ });
                $("#modal-cancel-button").on('click', function(ev){ });
            });
        },
        /** End of lifecycle */

        ask_confirmation: function(){
            $("#confirm_modal").modal('show');
            this.result = $.Deferred();
            return this.result.promise();
        },
    })

    return ConfirmModal;
})