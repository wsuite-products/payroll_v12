from odoo import models, fields, api, exceptions, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    disable_mail = fields.Boolean(string='Disable send mail', default=True)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res['disable_mail'] = self.env['ir.config_parameter'].sudo().get_param(
            'disable_mail')
        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('disable_mail',
                                                         self.disable_mail)
        super(ResConfigSettings, self).set_values()
