# Copyright 2020-TODAY Anand Kansagra <anandkansagra@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    slack_token = fields.Text(string='Slack Token')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res['slack_token'] = self.env['ir.config_parameter'].sudo().get_param('slack_token')
        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('slack_token', self.slack_token)
        super(ResConfigSettings, self).set_values()
