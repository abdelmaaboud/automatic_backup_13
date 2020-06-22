odoo.define('ks_office365_base.sync_base_message', function (require) {
    "use strict";

    var core = require('web.core');
    var _t = core._t;

    function ks_base_message(parent, action) {
        var self = parent;
        if (action.params.task == "warn") {
            self.do_warn(
                _t("Error"),
                _t(action.params.message)
            );
        }
        else if (action.params.task == "notify") {
            self.do_notify(
                _t("Warning"),
                _t(action.params.message)
            );
            self.do_action({
                type: 'ir.actions.act_window',
                name: 'Office 365 Logs',
                view_type: 'form',
                view_mode: 'tree,form',
                views: [[false, 'list'], [false, 'form']],
                res_model: 'ks_office365.logs',
            });
        }
    }
    core.action_registry.add("ks_base_message", ks_base_message);

});
