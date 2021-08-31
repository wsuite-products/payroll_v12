# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)
_test_logger = logging.getLogger('odoo.tests')

SMTP_TIMEOUT = 60


class IrMailServer(models.Model):
    _inherit = "ir.mail_server"
    _description = 'Mail Server'

    def connect(self, host=None, port=None, user=None,
                password=None, encryption=None,
                smtp_debug=False, mail_server_id=None):
        if self.env['ir.config_parameter'].sudo().get_param('disable_mail'):
            return False
        connection = super(IrMailServer, self).connect(
            host=host, port=port, user=user, password=password,
            encryption=encryption,
            smtp_debug=smtp_debug, mail_server_id=mail_server_id)
        return connection

    def build_email(self, email_from, email_to, subject, body, email_cc=None,
                    email_bcc=None, reply_to=False, attachments=None,
                    message_id=None, references=None, object_id=False,
                    subtype='plain', headers=None,
                    body_alternative=None, subtype_alternative='plain'):
        if self.env['ir.config_parameter'].sudo().get_param('disable_mail'):
            return True
        msg = super(IrMailServer, self).build_email(
            email_from, email_to, subject, body, email_cc=email_cc,
            email_bcc=email_bcc, reply_to=reply_to, attachments=attachments,
            message_id=message_id, references=references, object_id=object_id,
            subtype='html', headers=headers,
            body_alternative=body_alternative, subtype_alternative='plain')
        return msg

    @api.model
    def send_email(self, message, mail_server_id=None, smtp_server=None,
                   smtp_port=None,
                   smtp_user=None, smtp_password=None, smtp_encryption=None,
                   smtp_debug=False,
                   smtp_session=None):
        if self.env['ir.config_parameter'].sudo().get_param('disable_mail'):
            return False
        message_id = super(IrMailServer, self).send_email(
            message, mail_server_id=mail_server_id, smtp_server=smtp_server,
            smtp_port=smtp_port, smtp_user=smtp_user,
            smtp_password=smtp_password, smtp_encryption=smtp_encryption,
            smtp_debug=smtp_debug, smtp_session=smtp_session)
        return message_id
