from odoo import models, fields, api, _


###############
# Mail.Thread #
###############
class PRTMailThread(models.AbstractModel):
    _name = "mail.thread"
    _inherit = "mail.thread"

    hide_notifications = fields.Boolean(string="Hide notifications",
                                        help="Hide notifications - display messages only")

    """
    We may have readonly access to model so we need special method for RPC
    """
    @api.multi
    def write_sudo(self, vals):
        return self.sudo().write(vals)

    def read_sudo(self, fields=None, load='_classic_read'):
        return self.sudo().read(fields=fields, load=load)


################
# Mail.Message #
################
class PRTMailMessage(models.Model):
    _name = "mail.message"
    _inherit = "mail.message"

# -- Unlink
    @api.multi
    def unlink(self):

        # Store lead ids from messages in case we want to delete empty leads later
        lead_ids = []
        for rec in self.sudo():
            if rec.model == 'crm.lead':
                lead_ids.append(rec.res_id)

        # Unlink
        if self.env.user.has_group('prt_mail_messages_pro.group_lost'):
            # Check is deleting lost messages
            all_lost = True
            for rec in self.sudo():

                # Not lost? Unlink using actual user
                if rec.model and rec.res_id:
                    super(PRTMailMessage, self).unlink()
                    all_lost = False
                    break

            # All lost. Unlink using sudo
            if all_lost:
                super(PRTMailMessage, self.sudo()).unlink()
        else:
            super(PRTMailMessage, self).unlink()

        # Delete empty leads
        leads = self.env['crm.lead'].browse(lead_ids).filtered('company_id.lead_delete')
        leads_2_delete = self.env['crm.lead']

        for lead in leads:
            message_count = self.env['mail.message'].search_count([('res_id', '=', lead.id),
                                                                   ('model', '=', 'crm.lead'),
                                                                   ('message_type', '!=', 'notification')])
            if message_count == 0:
                leads_2_delete += lead

        # Delete leads with no messages
        if len(leads_2_delete) > 0:
            leads_2_delete.unlink()


#####################
# Mail Move Message #
#####################
class PRTMailMove(models.TransientModel):
    _name = 'prt.message.move.wiz'
    _inherit = 'prt.message.move.wiz'

    # -- Move messages
    @api.multi
    def message_move(self):
        self.ensure_one()
        if not self.model_to:
            return

        # Check is called from thread then take active ids
        thread_message_id = self._context.get('thread_message_id', False)
        message_ids = self._context.get('active_ids', False) if not thread_message_id else [thread_message_id]
        if not message_ids or len(message_ids) < 1:
                return

        dest_model = self.model_to._name
        dest_res_id = self.model_to.id
                
        messages = self.env['mail.message'].browse(message_ids)

        # Store leads from messages in case we want to delete empty leads later
        leads = False
        if self.lead_delete:
            lead_messages = self.env['mail.message'].search([('id', 'in', message_ids),
                                                             ('model', '=', 'crm.lead')])

            # Check if Opportunities are deleted as well
            if self.opp_delete:
                domain = [('id', 'in', lead_messages.mapped('res_id'))]
            else:
                domain = [('id', 'in', lead_messages.mapped('res_id')), ('type', '=', 'lead')]

            leads = self.env['crm.lead'].search(domain)
        # Move messages
        messages.sudo().write({'model': dest_model, 'res_id': dest_res_id})

        # Set parent to False from messages with parent from other record
        parent_change = messages.filtered('parent_id').filtered(lambda m: (m.parent_id.model != dest_model or m.parent_id.res_id != dest_res_id))

        if parent_change:
            parent_change.sudo().write({'parent_id': False})

        # Move attachments. Use sudo() to override access rules issues
        messages.mapped('attachment_ids').sudo().write({'res_model': dest_model, 'res_id': dest_res_id})

        # Notify followers of destination record
        if self.notify and self.notify != '0':
            subtype = 'mail.mt_note' if self.notify == '1' else 'mail.mt_comment'
            body = _("%s messages moved to this record:") % (str(len(messages)))
            # Add messages ref to body:
            i = 1
            url = self.env['ir.config_parameter'].sudo().get_param('web.base.url') + "/web#id="
            for message in messages:
                body += ((' <a target="_blank" href="%s">') % (url + str(message.id) + '&model=mail.message&view_type=form') +
                         (_("Message %s") % (str(i))) + '</a>')
                i += 1
            self.env[dest_model].browse([dest_res_id]).message_post(body=body, subject=_('Messages moved'),
                                                                    message_type='notification',
                                                                    subtype=subtype)

        # Delete empty leads
        if not leads:
            return

        # Compose list of leads to unlink
        leads_2_delete = self.env['crm.lead']
        for lead in leads:
            message_count = self.env['mail.message'].search_count([('res_id', '=', lead.id),
                                                                   ('model', '=', 'crm.lead'),
                                                                   ('message_type', '!=', 'notification')])
            if message_count == 0:
                leads_2_delete += lead

        # Delete leads with no messages
        if len(leads_2_delete) > 0:
            leads_2_delete.unlink()


###############
# Res.Company #
###############
class PRTCompany(models.Model):
    _name = "res.company"
    _inherit = "res.company"

    lead_delete = fields.Boolean(string="Delete empty leads",
                                 help="If all messages are moved from lead and there are no other messages"
                                      " left except for notifications lead will be deleted",
                                 readonly=False)
