from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    public_key = fields.Text(string='Public Key', related="company_id.jwt_private_key", readonly=False)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res['public_key'] = self.env['ir.config_parameter'].sudo().get_param('public_key')
        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('public_key', self.public_key)
        super(ResConfigSettings, self).set_values()
