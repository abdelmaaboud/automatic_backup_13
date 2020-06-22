
odoo.define('prt_mail_messages_pro.mail_settings_widget_extend', function (require) {
"use strict";

    var Followers = require('mail.Followers');
    var ThreadField = require('mail.ThreadField');
    var ChatThread = require('mail.ChatThread');
    var concurrency = require('web.concurrency');
    var core = require('web.core');
    var session = require('web.session');
    var data = require('web.data');
    var ActionManager = require('web.ActionManager');
    var chat_manager = require('mail.chat_manager');
    var Chatter = require('mail.Chatter');
    var _t = core._t;
    var QWeb = core.qweb;
    var time = require('web.time');
    var rpc = require('web.rpc');
    var config = require('web.config');

    var ORDER = {
        ASC: 1,
        DESC: -1,
    };


    Chatter.include({
        //action by click
        events: _.extend(Chatter.prototype.events, {
            'click .o_chatter_button_new_message': '_onOpenComposerMessage',
            'click .o_chatter_button_log_note': '_onOpenComposerNote',
            'click .o_chatter_button_schedule_activity': '_onScheduleActivity',
            'click .o_filter_checkbox': '_update',
        }),
        // public
        //read from DB from go record to record and NOT run start function
        update: function (record, fieldNames) {
            var self = this;
            if (typeof this.fields.thread !== typeof undefined && this.fields.thread !== false && typeof record.res_id !== typeof undefined && record.res_id !== false){
              if (this.fields.thread.model) {
                if (this.record.res_id !== record.res_id) {
                    this.fields.thread.res_id = record.res_id;
                    rpc.query({
                                model: this.fields.thread.model,
                                method: 'read_sudo',
                                args: [[this.fields.thread.res_id], ['hide_notifications']],

                            }).then(function(result){

                                if (result[0].hide_notifications){
                                    self.$('.o_filter_checkbox').prop("checked", true );
                                    _.extend(self.fields.thread.thread.options, {filter: 'yes',});
                                }
                                else{
                                    self.$('.o_filter_checkbox').prop( "checked", false );
                                    _.extend(self.fields.thread.thread.options, {filter: 'no',});
                                }

                               self.update(record);
                            });
                }
              }
            };
            this._super.apply(this, arguments);
        },
        //read from DB field hide_notifications and change checkbox and reload message
        start: function () {
            var res = this._super.apply(this, arguments);
            var self = this;
            if (typeof this.fields.thread !== typeof undefined && this.fields.thread !== false && typeof this.record !== typeof undefined && this.record !== false && typeof this.record.res_id !== typeof undefined && this.record.res_id !== false ){
              rpc.query({
                          model: this.fields.thread.model,
                          method: 'read_sudo',
                          args: [[this.record.res_id], ['hide_notifications']],

                      }).then(function(result){
                          if (result[0].hide_notifications){
                              self.$('.o_filter_checkbox').prop( "checked", true );
                              _.extend(self.fields.thread.thread.options, {filter: 'yes',});
                          }
                          else{
                              self.$('.o_filter_checkbox').prop( "checked", false );
                              _.extend(self.fields.thread.thread.options, {filter: 'no',});
                          }
                          self.trigger_up('reload');
                          //self.update(self.fields.thread.record);
                          });
                        };
            return res;
        },

        //Write to current model status checkbox and reload message (filtered)
        _update: function () {
            if (typeof this.fields.thread !== typeof undefined && this.fields.thread !== false){
              var check = false
              if (this.$('.o_filter_checkbox')[0].checked) {
                  _.extend(this.fields.thread.thread.options, {filter: 'yes',});
                  check = true
              }
              else
                  _.extend(this.fields.thread.thread.options, {filter: 'no',});

              rpc.query({
                          model: this.fields.thread.model,
                          method: 'write_sudo',
                          args: [[this.fields.thread.res_id], {
                                  hide_notifications: check,
              },],
                      })
              this.update(this.fields.thread.record);
            }
         },
    });


    ChatThread.include({

      events: _.extend(ChatThread.prototype.events, {
          "click a": "on_click_redirect",
          "click img": "on_click_redirect",
          "click strong": "on_click_redirect",
          "click .o_thread_show_more": "on_click_show_more",
          "click .o_attachment_download": "_onAttachmentDownload",
          "click .o_attachment_view": "_onAttachmentView",
          "click .o_thread_message_needaction": function (event) {
              var message_id = $(event.currentTarget).data('message-id');
              this.trigger("mark_as_read", message_id);
          },
          "click .o_thread_message_star": function (event) {
              var message_id = $(event.currentTarget).data('message-id');
              this.trigger("toggle_star_status", message_id);
          },
          "click .o_thread_message_reply": function (event) {
              this.selected_id = $(event.currentTarget).data('message-id');
              this.$('.o_thread_message').removeClass('o_thread_selected_message');
              this.$('.o_thread_message[data-message-id="' + this.selected_id + '"]')
                  .addClass('o_thread_selected_message');
              this.trigger('select_message', this.selected_id);
              event.stopPropagation();
          },
          "click .o_thread_message_reply_composer_quote": function (event) {
              var message_id = $(event.currentTarget).data('message-id');
              this.reply_composer('quote', message_id);
              event.stopPropagation();
          },
          "click .o_thread_message_reply_composer_forward": function (event) {
              var message_id = $(event.currentTarget).data('message-id');
              this.reply_composer('forward', message_id);
              event.stopPropagation();
          },
          "click .o_thread_message_reply_composer_move": function (event) {
              var self = this;
              var message_id = $(event.currentTarget).data('message-id');
              var action = {
                  type: 'ir.actions.act_window',
                  res_model: 'prt.message.move.wiz',
                  view_mode: 'form',
                  view_type: 'form',
                  views: [[false, 'form']],
                  target: 'new',
                  context: {thread_message_id:message_id},
              };
              self.do_action(action, {
                  on_close: self.trigger_up.bind(self, 'reload')});
              event.stopPropagation();
          },
          "click .oe_mail_expand": function (event) {
              event.preventDefault();
              var $message = $(event.currentTarget).parents('.o_thread_message');
              $message.addClass('o_message_expanded');
              this.expanded_msg_ids.push($message.data('message-id'));
          },
          "click .o_thread_message": function (event) {
              $(event.currentTarget).toggleClass('o_thread_selected_message');
          },
          "click": function () {
              if (this.selected_id) {
                  this.unselect();
                  this.trigger('unselect_message');
              }
          },
      }),

      reply_composer: function(wiz_mode, message_id) {
            var self = this;
            rpc.query({
              model: 'mail.message',
              method: 'reply_prep_context',
              args: [[message_id]],
              context: {wizard_mode:wiz_mode}
            }).then(function(result){
              var action = {
                  type: 'ir.actions.act_window',
                  res_model: 'mail.compose.message',
                  view_mode: 'form',
                  view_type: 'form',
                  views: [[false, 'form']],
                  target: 'new',
                  context: result,
              };
              self.do_action(action, {
                  on_close: self.trigger_up.bind(self, 'reload')});})
      },

      render: function (messages, options) {
          var self = this;
          var msgs = _.map(messages, this._preprocess_message.bind(this));
          if (this.options.display_order === ORDER.DESC) {
              msgs.reverse();
          }
          options = _.extend({}, this.options, options);

          // Hide avatar and info of a message if that message and the previous
          // one are both comments wrote by the same author at the same minute
          // and in the same document (users can now post message in documents
          // directly from a channel that follows it)
          var prev_msg;
          _.each(msgs, function (msg) {
              if (!prev_msg || (Math.abs(msg.date.diff(prev_msg.date)) > 60000) ||
                  prev_msg.message_type !== 'comment' || msg.message_type !== 'comment' ||
                  (prev_msg.author_id[0] !== msg.author_id[0]) || prev_msg.model !== msg.model ||
                  prev_msg.res_id !== msg.res_id) {
                  msg.display_author = true;
              } else {
                  msg.display_author = !options.squash_close_messages;
              }
              prev_msg = msg;
          });
          if (options.filter == 'yes')
              msgs = _.filter(msgs, function(msg){ return (msg.message_type == 'comment' || msg.message_type == 'email' ); });

          this.$el.html(QWeb.render('mail.ChatThread', {
              messages: msgs,
              options: options,
              ORDER: ORDER,
              date_format: time.getLangDatetimeFormat(),
          }));

          this.attachments = _.uniq(_.flatten(_.map(messages, 'attachment_ids')));

          _.each(msgs, function(msg) {
              var $msg = self.$('.o_thread_message[data-message-id="'+ msg.id +'"]');
              $msg.find('.o_mail_timestamp').data('date', msg.date);

              self.insert_read_more($msg);
          });

          if (!this.update_timestamps_interval) {
              this.update_timestamps_interval = setInterval(function() {
                  self.update_timestamps();
              }, 1000*60);
          }
      },
    });
});
