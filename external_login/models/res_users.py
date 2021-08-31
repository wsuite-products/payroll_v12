# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import AccessDenied, UserError
from odoo.addons.auth_signup.models.res_users import SignupError
import jwt


class ResUsers(models.Model):
    _inherit = 'res.users'

    microsoft_refresh_token = fields.Char('Microsoft Refresh Token')
    wadmin_refresh_token = fields.Char('Microsoft Refresh Token')

    def _check_credentials(self, password):
        try:
            return super(ResUsers, self)._check_credentials(password)
        except AccessDenied:
            res = self.sudo().search([('id', '=', self.env.uid), ('oauth_access_token', '=', password)])
            if len(password) > 750:
                decode_token = jwt.decode(password, verify=False)
                user = decode_token.get('username')
                if not user:
                    user = decode_token.get('email')
                if not res:
                    res = self.sudo().search([('id', '=', self.env.uid), ('login', '=', user)])
            if not res:
                raise

    @api.model
    def _microsoft_generate_signup_values(self, provider, params):
        email = params.get('email')
        return {
            'name': params.get('name', email),
            'login': email,
            'email': email,
            'oauth_provider_id': provider,
            'oauth_uid': params['user_id'],
            'oauth_access_token': params['access_token'],
            'active': True,
            'microsoft_refresh_token': params.get('microsoft_refresh_token',
                                                  ''),
            'wadmin_refresh_token': params.get('wadmin_refresh_token', ''),
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
        }

    @api.model
    def _microsoft_auth_oauth_signin(self, provider, params):
        try:
            oauth_uid = params['user_id']
            users = self.sudo().search([
                ("oauth_uid", "=", oauth_uid),
                ('oauth_provider_id', '=', provider)
            ], limit=1)
            if not users:
                users = self.sudo().search([
                    ("login", "=", params.get('email'))
                ], limit=1)
            if not users:
                raise AccessDenied()
            assert len(users.ids) == 1
            vals = {'oauth_access_token': params['access_token']}
            provider_wsuite = self.env.ref(
                'external_login.provider_wsuite')
            if provider == provider_wsuite.id:
                vals.update({'wadmin_refresh_token':
                                 params['wadmin_refresh_token']})
            else:
                vals.update({'microsoft_refresh_token':
                                 params['microsoft_refresh_token']})
            users.sudo().write(vals)
            # users.sudo().write({
            #     'oauth_access_token': params['access_token'],
            #     'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
            #     'microsoft_refresh_token': params['microsoft_refresh_token']})
            return users.login
        except AccessDenied as access_denied_exception:
            if self._context and self._context.get('no_user_creation'):
                return None
            raise access_denied_exception
            # values = self._microsoft_generate_signup_values(provider, params)
            # try:
            #     _, login, _ = self.signup(values)
            #     return login
            # except (SignupError, UserError):
            #     raise access_denied_exception

    @api.model
    def microsoft_auth_oauth(self, provider, params):
        access_token = params.get('access_token')
        login = self._microsoft_auth_oauth_signin(provider, params)
        if not login:
            raise AccessDenied()
        # return user credentials
        return self._cr.dbname, login, access_token
