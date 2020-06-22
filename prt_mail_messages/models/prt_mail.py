from odoo import models, fields, api, _, tools
import logging
from odoo.exceptions import MissingError

_logger = logging.getLogger(__name__)

TREE_VIEW_ID = False
FORM_VIEW_ID = False


################
# Mail.Message #
################
class PRTMailMessage(models.Model):
    _name = "mail.message"
    _inherit = "mail.message"

    author_display = fields.Char(string="Author", compute="_author_display")

    # Fields to avoid access check issues
    author_allowed_id = fields.Many2one(string="Author", comodel_name='res.partner',
                                        compute='_get_author_allowed',
                                        search='_search_author_allowed')

    partner_allowed_ids = fields.Many2many(string="Recipients", comodel_name='res.partner',
                                           compute='_get_partners_allowed')

    subject_display = fields.Char(string="Subject", compute="_subject_display")
    partner_count = fields.Integer(string="Recipients count", compute='_partner_count')
    record_ref = fields.Reference(string="Message Record", selection='_referenceable_models',
                                  compute='_record_ref')
    attachment_count = fields.Integer(string="Attachments count", compute='_attachment_count')
    thread_messages_count = fields.Integer(string="Messages in thread", compute='_thread_messages_count',
                                           help="Total number of messages in thread")
    ref_partner_ids = fields.Many2many(string="Followers", comodel_name='res.partner',
                                       compute='_message_followers')
    ref_partner_count = fields.Integer(string="Followers", compute='_ref_partner_count')

# -- Count ref Partners
    @api.multi
    def _ref_partner_count(self):
        for rec in self:
            rec.ref_partner_count = len(rec.ref_partner_ids)

    """
    Sometimes user has access to record but does not have access to author or recipients.
    Below is a workaround for author, recipient and followers
    """
# -- Get allowed author
    @api.depends('author_id')
    @api.multi
    def _get_author_allowed(self):
        for rec in self:
                author_id = rec.author_id
                try:
                    author_id.check_access_rule('read')
                    rec.author_allowed_id = author_id
                except:
                    continue

# -- Get allowed recipients
    @api.depends('partner_ids')
    @api.multi
    def _get_partners_allowed(self):
        for rec in self:
            recipients_allowed = self.env['res.partner']
            for partner in rec.partner_ids:
                try:
                    partner.check_access_rule('read')
                    recipients_allowed += partner
                except:
                    continue
            rec.partner_allowed_ids = recipients_allowed

# -- Search allowed authors
    @api.model
    def _search_author_allowed(self, operator, value):
        return [('author_id', operator, value)]

# -- Get related record followers
    """
    Check if model has 'followers' field and user has access to followers
    """
    @api.depends('record_ref')
    @api.multi
    def _message_followers(self):
        for rec in self:
            if rec.record_ref:
                if 'message_partner_ids' in self.env[rec.model]._fields:
                    followers_allowed = self.env['res.partner']
                    for follower in rec.record_ref.message_partner_ids:
                        try:
                            follower.check_access_rule('read')
                            followers_allowed += follower
                        except:
                            continue
                    rec.ref_partner_ids = followers_allowed


# -- Dummy
    @api.multi
    def dummy(self):
        return

# -- Get Subject for tree view
    @api.depends('subject')
    @api.multi
    def _subject_display(self):

        # Get model names first. Use this method to get translated values
        ir_models = self.env['ir.model'].search([('model', 'in', list(set(self.mapped('model'))))])
        model_dict = {}
        for model in ir_models:
            # Check if model has "name" field
            has_name = self.env['ir.model.fields'].sudo().search_count([('model_id', '=', model.id),
                                                                        ('name', '=', 'name')])
            model_dict.update({model.model: [model.name, has_name]})

        # Compose subject
        for rec in self:
            if rec.subject:
                subject_display = rec.subject
            else:
                subject_display = '=== No Reference ==='

            # Has reference
            if rec.record_ref:
                subject_display = model_dict.get(rec.model)[0]

                # Has 'name' field
                if model_dict.get(rec.model, False)[1]:
                    try:
                        subject_display = "%s: %s" % (subject_display, rec.record_ref.sudo().name)
                    except AttributeError:
                        pass

                # Has subject
                if rec.subject:
                    subject_display = "%s => %s" % (subject_display, rec.subject)

            # Set subject
            rec.subject_display = subject_display

# -- Get Author for tree view
    @api.depends('author_allowed_id')
    @api.multi
    def _author_display(self):
        for rec in self:
            rec.author_display = rec.author_allowed_id.name if rec.author_allowed_id else rec.email_from

# -- Count recipients
    @api.depends('partner_allowed_ids')
    @api.multi
    def _partner_count(self):
        for rec in self:
            rec.partner_count = len(rec.partner_allowed_ids)

# -- Count attachments
    @api.depends('attachment_ids')
    @api.multi
    def _attachment_count(self):
        for rec in self:
            rec.attachment_count = len(rec.attachment_ids)

# -- Count messages in same thread
    @api.depends('res_id')
    @api.multi
    def _thread_messages_count(self):
        for rec in self:
            rec.thread_messages_count = self.search_count(['&', '&',
                                                           ('model', '=', rec.model),
                                                           ('res_id', '=', rec.res_id),
                                                           ('message_type', '!=', 'notification')])

# -- Ref models
    @api.model
    def _referenceable_models(self):
        # return [(x.model, x.name) for x in self.env['ir.model'].sudo().search([('model', '!=', 'mail.channel')])]
        """
        Mail channel is needed for legacy views (Settings->Technical Settings->Messages)
        """
        return [(x.model, x.name) for x in self.env['ir.model'].sudo().search([('transient', '=', False)])]

# -- Compose reference
    @api.depends('res_id')
    @api.multi
    def _record_ref(self):
        for rec in self:
            if rec.model:
                if rec.res_id:
                    res = self.env[rec.model].sudo().search([("id", "=", rec.res_id)])
                    if res:
                        rec.record_ref = res


# -- Open messages of the same thread
    @api.multi
    def thread_messages(self):
        self.ensure_one()

        global TREE_VIEW_ID
        global FORM_VIEW_ID

        # Cache Tree View and Form View ids
        if not TREE_VIEW_ID:
            TREE_VIEW_ID = self.env.ref('prt_mail_messages.prt_mail_message_tree').id
            FORM_VIEW_ID = self.env.ref('prt_mail_messages.prt_mail_message_form').id

        return {
            'name': _("Messages"),
            "views": [[TREE_VIEW_ID, "tree"], [FORM_VIEW_ID, "form"]],
            'res_model': 'mail.message',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('message_type', '!=', 'notification'), ('model', '=', self.model), ('res_id', '=', self.res_id)]
        }

# -- Override _search
    """
    mail.message overrides generic '_search' defined in 'model' to implement own logic for message access rights.
    However sometimes it does not work as expected.
    So we use generic method in 'model' and check access rights later in 'search' method.
    Following keys in context are used:
        - 'check_messages_access': if not set legacy 'search' is performed
    """
    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):

        if not self._context.get('check_messages_access', False):
            return super(PRTMailMessage, self)._search(args=args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)

        if expression.is_false(self, args):
            # optimization: no need to query, as no record satisfies the domain
            return 0 if count else []

        query = self._where_calc(args)
        order_by = self._generate_order_by(order, query)
        from_clause, where_clause, where_clause_params = query.get_sql()

        where_str = where_clause and (" WHERE %s" % where_clause) or ''

        if count:
            # Ignore order, limit and offset when just counting, they don't make sense and could
            # hurt performance
            query_str = 'SELECT count(1) FROM ' + from_clause + where_str
            self._cr.execute(query_str, where_clause_params)
            res = self._cr.fetchone()
            return res[0]

        limit_str = limit and ' limit %d' % limit or ''
        offset_str = offset and ' offset %d' % offset or ''
        query_str = 'SELECT "%s".id FROM ' % self._table + from_clause + where_str + order_by + limit_str + offset_str
        self._cr.execute(query_str, where_clause_params)
        res = self._cr.fetchall()

        # TDE note: with auto_join, we could have several lines about the same result
        # i.e. a lead with several unread messages; we uniquify the result using
        # a fast way to do it while preserving order (http://www.peterbe.com/plog/uniqifiers-benchmark)
        def _uniquify_list(seq):
            seen = set()
            return [x for x in seq if x not in seen and not seen.add(x)]

        return _uniquify_list([x[0] for x in res])

# -- Override read
    """
    Avoid access rights check implemented in original mail.message
    Will check them later in "search"
    Using base model function instead
        Following keys in context are used:
        - 'check_messages_access': if not set legacy 'search' is performed
    """
    @api.multi
    def read(self, fields=None, load='_classic_read'):

        if not self._context.get('check_messages_access', False):
            return super(PRTMailMessage, self).read(fields=fields, load=load)

        """
        From here starts the original 'read' code
        """
        # split fields into stored and computed fields
        stored, inherited, computed = [], [], []
        for name in fields:
            field = self._fields.get(name)
            if field:
                if field.store:
                    stored.append(name)
                elif field.base_field.store:
                    inherited.append(name)
                else:
                    computed.append(name)
            else:
                _logger.warning("%s.read() with unknown field '%s'", self._name, name)

        # fetch stored fields from the database to the cache; this should feed
        # the prefetching of secondary records
        self._read_from_database(stored, inherited)

        # retrieve results from records; this takes values from the cache and
        # computes remaining fields
        result = []
        name_fields = [(name, self._fields[name]) for name in (stored + inherited + computed)]
        use_name_get = (load == '_classic_read')

        for record in self:
            try:
                values = {'id': record.id}
                for name, field in name_fields:
                    values[name] = field.convert_to_read(record[name], record, use_name_get)
                result.append(values)
            except MissingError:
                pass

        return result

# -- Override Search
    """
    Mail message access rights/rules checked must be done based on the access rights/rules of the message record.
    As a workaround we are using 'search' method to filter messages from unavailable records.
    
    Display only messages where user has read access to related record.
    
    Following keys in context are used:
    - 'check_messages_access': if not set legacy 'search' is performed
    - 'force_record_reset': in case message refers to non-existing (e.g. removed) record model and res_id will be set NULL
    """
    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):

        if not self._context.get('check_messages_access', False):
            return super(PRTMailMessage, self).search(args=args, offset=offset, limit=limit, order=order, count=count)

        # Store context keys
        force_record_reset = self._context.get('force_record_reset', False)
        # Store initial args in case we need them later
        modded_args = args
        sort_order = 'desc' if order == 'date DESC, id DESC' else 'asc'

        # New query
        # Check model access 1st
        # Add mail.channel by default because we are not showing chat/channel messages
        forbidden_models = ['mail.channel']

        # Get list of possible followed models
        self._cr.execute(""" SELECT model FROM ir_model mdl
                                WHERE mdl.is_mail_thread = True 
                                AND name != 'mail.channel' """)

        # Check each model
        for msg_model in self._cr.fetchall():
            if not self.env['ir.model.access'].check(msg_model[0], 'read', raise_exception=False):
                forbidden_models.append(msg_model[0])

        # Add forbidden models condition to domain
        if len(forbidden_models) > 0:
            modded_args.append(['model', 'not in', forbidden_models])

        # Return Count
        if count:
            return super(PRTMailMessage, self).search(args=modded_args, offset=offset, limit=limit, order=order, count=True)

        # Get records
        res_ids = self._search(args=modded_args, offset=offset, limit=limit, order=order, count=False)
        res = self.browse(res_ids)
        # Now check record rules
        res_allowed = self.env['mail.message']
        len_initial = limit if limit else len(res)
        len_filtered = 0
        last_val = False

        # Check records
        """
        Check in we need include "lost" messages. These are messages with no model or res_id
        """
        get_lost = self._context.get('get_lost', False)

        for rec in res:
            last_val = rec.date

            # No model
            if not rec.model:
                if get_lost:
                    res_allowed += rec
                    len_filtered += 1
                continue

            # No id
            if not rec.res_id:
                if get_lost:
                    res_allowed += rec
                    len_filtered += 1
                continue

            # Check access rules on record. Skip if refers to deleted record
            try:
                target_rec = self.env[rec.model].search([('id', '=', rec.res_id)])
                if not target_rec:
                    # Reset model and res_id
                    if force_record_reset:
                        rec.sudo().write({'model': False, 'res_id': False})
                    continue
                # Check message record
                target_rec.check_access_rule('read')
            except:
                continue

            res_allowed += rec
            len_filtered += 1

        # We store ids of the record with the last date not to fetch them twice while fetching more recs
        last_ids = res.filtered(lambda d: d.date == last_val).ids

        del res  # Hope Python will free memory asap!))

        # Return if initially got less then limit
        if limit is None or len_initial < limit:
            return res_allowed

        len_remaining = len_initial - len_filtered

        # Return if all allowed
        if len_remaining == 0:
            return res_allowed

        # Get remaining recs
        while len_remaining > 0:
            if sort_order == 'desc':
                new_args = modded_args + [['date', '<=', last_val], ['id', 'not in', last_ids]]
            else:
                new_args = modded_args + [['date', '>=', last_val], ['id', 'not in', last_ids]]

            # Let's try!))
            res_2_ids = self._search(args=new_args, offset=0, limit=len_remaining, order=order, count=False)
            res_2 = self.browse(res_2_ids)

            if len(res_2) < 1:
                break

            # Check records
            for rec in res_2:
                last_val = rec.date

                # No model
                if not rec.model:
                    if get_lost:
                        res_allowed += rec
                        len_filtered += 1
                    continue

                # No res_id
                if not rec.res_id:
                    if get_lost:
                        res_allowed += rec
                        len_filtered += 1
                    continue

                # Check access rules on record. Skip if refers to deleted record
                try:
                    target_rec = self.env[rec.model].search([('id', '=', rec.res_id)])
                    if not target_rec:
                        # Reset model and res_id
                        if force_record_reset:
                            rec.sudo().write({'model': False, 'res_id': False})
                        continue
                    # Check message record
                    target_rec.check_access_rule('read')
                except:
                    continue

                res_allowed += rec
                len_remaining -= 1

            if not len_remaining == 0:
                last_ids += res_2.filtered(lambda d: d.date == last_val).ids

        return res_allowed

# -- Prepare context for reply or quote message
    @api.multi
    def reply_prep_context(self):
        self.ensure_one()
        body = False
        wizard_mode = self._context.get('wizard_mode', False)

        if wizard_mode in ['quote', 'forward']:
            body = (_(
                "<div font-style=normal;><br/></div><blockquote>----- Original message ----- <br/> Date: %s <br/> From: %s <br/> Subject: %s <br/><br/>%s</blockquote>") %
                    (str(self.date), self.author_display, self.subject_display, self.body))

        ctx = {
            'default_res_id': self.res_id,
            'default_parent_id': False if wizard_mode == 'forward' else self.id,
            'default_model': self.model,
            'default_partner_ids': [self.author_allowed_id.id] if self.author_allowed_id else [],
            'default_attachment_ids': self.attachment_ids.ids if wizard_mode == 'forward' else [],
            'default_is_log': False,
            'default_body': body,
            'default_wizard_mode': wizard_mode
        }
        return ctx

# -- Reply or quote message
    @api.multi
    def reply(self):
        self.ensure_one()

        return {
            'name': _("New message"),
            "views": [[False, "form"]],
            'res_model': 'mail.compose.message',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': self.reply_prep_context()
        }


# -- Move message
    @api.multi
    def move(self):
        self.ensure_one()

        return {
            'name': _("Move messages"),
            "views": [[False, "form"]],
            'res_model': 'prt.message.move.wiz',
            'type': 'ir.actions.act_window',
            'target': 'new'
        }


#####################
# Mail Move Message #
#####################
class PRTMailMove(models.TransientModel):
    _name = 'prt.message.move.wiz'
    _description = 'Move Messages To Other Thread'

    model_to = fields.Reference(string="Move to", selection='_referenceable_models')
    lead_delete = fields.Boolean(string="Delete Empty Leads",
                                 help="If all messages are moved from lead and there are no other messages"
                                      " left except for notifications lead will be deleted")
    opp_delete = fields.Boolean(string="Delete Empty Opportunities",
                                help="If all messages are moved from opportunity and there are no other messages"
                                     " left except for notifications opportunity will be deleted")

    notify = fields.Selection([
        ('0', 'Do not notify'),
        ('1', 'Log internal note'),
        ('2', 'Send message'),
    ], string="Notify", required=True,
        default='0',
        help="Notify followers of destination record")

# -- Ref models
    @api.model
    def _referenceable_models(self):
        return [(x.object, x.name) for x in self.env['res.request.link'].sudo().search([])]


################
# Res.Partner #
################
class PRTPartner(models.Model):
    _name = "res.partner"
    _inherit = "res.partner"

    messages_from_count = fields.Integer(string="Messages From", compute='_messages_from_count')
    messages_to_count = fields.Integer(string="Messages To", compute='_messages_to_count')

# -- Count messages from
    @api.depends('message_ids')
    @api.multi
    def _messages_from_count(self):
        for rec in self:
            if rec.id:
                rec.messages_from_count = self.env['mail.message'].search_count([('author_id', 'child_of', rec.id),
                                                                                 ('message_type', '!=', 'notification'),
                                                                                 ('model', '!=', 'mail.channel')])
            else:
                rec.messages_from_count = 0

# -- Count messages from
    @api.depends('message_ids')
    @api.multi
    def _messages_to_count(self):
        for rec in self:
            rec.messages_to_count = self.env['mail.message'].search_count([('partner_ids', 'in', [rec.id]),
                                                                           ('message_type', '!=', 'notification'),
                                                                           ('model', '!=', 'mail.channel')])

# -- Open related
    @api.multi
    def partner_messages(self):
        self.ensure_one

        # Choose what messages to display
        open_mode = self._context.get('open_mode', 'from')

        if open_mode == 'from':
            domain = [('message_type', '!=', 'notification'),
                      ('author_id', 'child_of', self.id),
                      ('model', '!=', 'mail.channel')]
        else:
            domain = [('message_type', '!=', 'notification'),
                      ('partner_ids', 'in', [self.id]),
                      ('model', '!=', 'mail.channel')]

        # Cache Tree View and Form View ids
        global TREE_VIEW_ID
        global FORM_VIEW_ID

        if not TREE_VIEW_ID:
            TREE_VIEW_ID = self.env.ref('prt_mail_messages.prt_mail_message_tree').id
            FORM_VIEW_ID = self.env.ref('prt_mail_messages.prt_mail_message_form').id

        return {
            'name': _("Messages"),
            "views": [[TREE_VIEW_ID, "tree"], [FORM_VIEW_ID, "form"]],
            'res_model': 'mail.message',
            'type': 'ir.actions.act_window',
            'context': "{'check_messages_access': True}",
            'target': 'current',
            'domain': domain
        }

# -- Send email from partner's form view
    @api.multi
    def send_email(self):
        self.ensure_one()

        return {
            'name': _("New message"),
            "views": [[False, "form"]],
            'res_model': 'mail.compose.message',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_res_id': False,
                'default_parent_id': False,
                'default_model': False,
                'default_partner_ids': [self.id],
                'default_attachment_ids': False,
                'default_is_log': False,
                'default_body': False,
                'default_wizard_mode': 'compose'
            }
        }


########################
# Mail.Compose Message #
########################
class PRTMailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'
    _name = 'mail.compose.message'

    wizard_mode = fields.Char(string="Wizard mode")
    forward_ref = fields.Reference(string="Attach to record", selection='_referenceable_models_fwd',
                                   readonly=False)

# -- Ref models
    @api.model
    def _referenceable_models_fwd(self):
        return [(x.object, x.name) for x in self.env['res.request.link'].sudo().search([])]

# -- Record ref change
    @api.onchange('forward_ref')
    @api.multi
    def ref_change(self):
        self.ensure_one()
        if self.forward_ref:
            self.update({
                'model': self.forward_ref._name,
                'res_id': self.forward_ref.id
            })

# -- Get record data
    @api.model
    def get_record_data(self, values):
        """
        Copy-pasted mail.compose.message original function so stay aware in case it is changed in Odoo core!

        Returns a defaults-like dict with initial values for the composition
        wizard when sending an email related a previous email (parent_id) or
        a document (model, res_id). This is based on previously computed default
        values. """
        result = {}
        subj = self._context.get('default_subject', False)
        subject = tools.ustr(subj) if subj else False
        if not subject:
            if values.get('parent_id'):
                parent = self.env['mail.message'].browse(values.get('parent_id'))
                result['record_name'] = parent.record_name,
                subject = tools.ustr(parent.subject or parent.record_name or '')
                if not values.get('model'):
                    result['model'] = parent.model
                if not values.get('res_id'):
                    result['res_id'] = parent.res_id
                partner_ids = values.get('partner_ids', list()) +\
                              [(4, id) for id in parent.partner_ids.filtered(lambda rec: rec.email not in [self.env.user.email, self.env.user.company_id.email]).ids]
                if self._context.get('is_private') and parent.author_id:  # check message is private then add author also in partner list.
                    partner_ids += [(4, parent.author_id.id)]
                result['partner_ids'] = partner_ids
            elif values.get('model') and values.get('res_id'):
                doc_name_get = self.env[values.get('model')].browse(values.get('res_id')).name_get()
                result['record_name'] = doc_name_get and doc_name_get[0][1] or ''
                subject = tools.ustr(result['record_name'])

            # Change prefix in case we are forwarding
            re_prefix = _('Fwd:') if self._context.get('default_wizard_mode', False) == 'forward' else _('Re:')

            if subject and not (subject.startswith('Re:') or subject.startswith(re_prefix)):
                subject = "%s %s" % (re_prefix, subject)

        result['subject'] = subject

        return result

# Legacy! keep those imports here to avoid dependency cycle errors
from odoo.osv import expression