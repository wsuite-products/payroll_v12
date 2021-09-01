# Copyright 2019-TODAY WSuite Products <wsuite-products@destiny.ws>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models
from odoo.osv import expression


class MailMessage(models.Model):
    """For read message."""

    _inherit = 'mail.message'

    @api.multi
    def set_message_done(self):
        """For read message."""
        partner_id = self.env.user.partner_id
        notifications = self.env['mail.notification'].sudo().search([
            ('mail_message_id', 'in', self.ids),
            ('res_partner_id', '=', partner_id.id),
            ('is_read', '=', False)])
        for notification in notifications:
            notification.mail_message_id.sudo().write(
                {'starred_partner_ids': [(4, self.env.user.partner_id.id)]})
        return super(MailMessage, self).set_message_done()

    @api.model
    def mark_all_as_read(self, channel_ids=None, domain=None):
        """ Remove all needactions of the current partner. If channel_ids is
            given, restrict to messages written in one of those channels. """
        partner_id = self.env.user.partner_id.id
        # delete employee notifs, keep customer ones
        delete_mode = not self.env.user.share
        if not domain and delete_mode:
            query = "DELETE FROM mail_message_res_partner_needaction_rel WHERE res_partner_id IN %s"
            args = [(partner_id,)]
            if channel_ids:
                query += """
                    AND mail_message_id in
                        (SELECT mail_message_id
                        FROM mail_message_mail_channel_rel
                        WHERE mail_channel_id in %s)"""
                args += [tuple(channel_ids)]
            query += " RETURNING mail_message_id as id"
            self._cr.execute(query, args)
            self.invalidate_cache()

            ids = [m['id'] for m in self._cr.dictfetchall()]
            for message in ids:
                self.browse(message).sudo().write(
                    {'starred_partner_ids': [
                        (4, partner_id)]})
        else:
            # not really efficient method: it does one db request for the
            # search, and one for each message in the result set to remove the
            # current user from the relation.
            msg_domain = [('needaction_partner_ids', 'in', partner_id)]
            if channel_ids:
                msg_domain += [('channel_ids', 'in', channel_ids)]
            unread_messages = self.search(expression.AND([msg_domain, domain]))
            notifications = self.env['mail.notification'].sudo().search([
                ('mail_message_id', 'in', unread_messages.ids),
                ('res_partner_id', '=', self.env.user.partner_id.id),
                ('is_read', '=', False)])
            for notification in notifications:
                notification.mail_message_id.sudo().write(
                    {'starred_partner_ids': [(4, self.env.user.partner_id.id)]})
            if delete_mode:
                notifications.unlink()
            else:
                notifications.write({'is_read': True})
            ids = unread_messages.mapped('id')

        notification = {'type': 'mark_as_read',
                        'message_ids': ids, 'channel_ids': channel_ids}
        self.env['bus.bus'].sendone(
            (self._cr.dbname, 'res.partner', self.env.user.partner_id.id), notification)

        return ids
