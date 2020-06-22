odoo.define("barcode_scanner.VideoScanner", function(require){
    var Widget = require("web.Widget");
    var Dialog = require("web.Dialog");
    var core = require('web.core');
    var qweb = core.qweb;
    var _t = core._t;

    const codeReader = new ZXing.BrowserMultiFormatReader();

    /* Widget to scan with a camera from the device */
    var VideoScaner = Widget.extend({
        init: function(parent){
            var self = this;
            self.parent = parent;
            this._super.apply(this, arguments);
            // Dialog destroy method overrided to reset the video code reader
            Dialog = Dialog.extend({
                destroy: function(){
                    this._super.apply(this,arguments);
                    codeReader.reset();
                }
            })
        },
        willStart: function(){
            return $.when(this._super.apply(this, arguments));
        },
        start: function(){
            return $.when(this._super.apply(this, arguments));
        },
        destroy: function(){
            return $.when(this._super.apply(this, arguments)).then(function(){
                $(this).empty();
            });
        },
        /* 
            Open a dialog with a video and scan the barcode.
            Return -> Scanned barcode as a promise
        */
        scan_barcode: function(){
            var barcode = $.Deferred();
            var dialog = this._open_dialog();
            codeReader.getVideoInputDevices()
            .then((devideIds) => {
                let selected = devideIds[0].devideId;
                codeReader.decodeOnceFromVideoDevice(selected, "video_scanner")
                .then((data)=> {
                    barcode.resolve(data.text);
                    dialog.close();
                    codeReader.reset();
                })
            })
            return barcode.promise();
        },
        _open_dialog: function(){
            var dialog = new Dialog(this,{
                title: _t("Video Scanner"),
                $content: qweb.render("barcode_scanner.video_scanner"),
                buttons: [{
                    text: _t("Close"),
                    click: function(){
                        this.close();
                    },
                    close: true
                }]
            })
            dialog.open();
            return dialog;
        }
    });

    return VideoScaner;

});