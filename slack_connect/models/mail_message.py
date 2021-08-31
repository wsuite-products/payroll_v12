# Copyright 2020-TODAY Anand Kansagra <anandkansagra@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from slack import WebClient
from slack.errors import SlackApiError

from odoo import api, models


class MailMessage(models.Model):
    _inherit = 'mail.message'

    @api.model
    def create(self, vals):
        res = super(MailMessage, self).create(vals)
        if vals.get('record_name', '') and vals.get('body', '') and\
                vals.get('message_type', '') == 'comment':
            slack_token = self.env['ir.config_parameter'].sudo().get_param(
                'slack_token')
            if slack_token:
                client = WebClient(token=slack_token)
                try:
                    message = vals.get('body', '') + '\n' +\
                        'From:- WERP' + '\nUser:- ' + self.env.user.login
                    response = client.chat_postMessage(
                        channel='#' + vals.get('record_name', ''),
                        text=message)
                    assert response["message"]["text"] == message
                except SlackApiError as e:
                    # You will get a SlackApiError if "ok" is False
                    assert e.response["ok"] is False
                    # str like 'invalid_auth', 'channel_not_found'
                    assert e.response["error"]
        return res
