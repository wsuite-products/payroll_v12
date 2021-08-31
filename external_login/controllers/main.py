# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

import logging
import requests
import json
import odoo
import jwt
import http.client as httplib
import simplejson
import werkzeug.utils
from odoo import http
from odoo.http import request
from odoo.addons.auth_oauth.controllers.main \
    import OAuthLogin as Home
from odoo.addons.web.controllers.main \
    import set_cookie_and_redirect, login_and_redirect
from odoo.addons.auth_oauth.controllers.main \
    import fragment_to_query_string
from odoo.addons.web.controllers.main import Session as ses
from odoo.exceptions import AccessDenied

_logger = logging.getLogger(__name__)


class OAuthLogin(Home):

    def list_providers(self):
        try:
            providers = request.env['auth.oauth.provider'].sudo().search_read(
                [('enabled', '=', True)])
        except Exception:
            providers = []
        provider_microsoft = request.env.ref(
            'external_login.provider_microsoft')
        provider_wsuite = request.env.ref(
            'external_login.provider_wsuite')
        base_url = request.env['ir.config_parameter'].sudo().get_param(
            'web.base.url')
        for provider in providers:
            if provider.get('id') == provider_microsoft.id:
                return_url = base_url + '/auth_oauth/microsoft/signin'
                params = dict(
                    client_id=provider['client_id'],
                    response_type='code',
                    scope=provider['scope'],
                    redirect_uri=return_url,
                )
            elif provider.get('id') == provider_wsuite.id:
                return_url = base_url + '/auth_oauth/wadmin/signin'
                state = self.get_state(provider)
                params = dict(
                    client_id=provider['client_id'],
                    redirect_uri=return_url,
                    scope='',
                    response_type='code',
                    state=json.dumps(state),
                )
            else:
                return_url = base_url + '/auth_oauth/signin'
                state = self.get_state(provider)
                params = dict(
                    response_type='token',
                    client_id=provider['client_id'],
                    redirect_uri=return_url,
                    scope=provider['scope'],
                    state=json.dumps(state),
                )
            provider['auth_link'] = "%s?%s" % (provider['auth_endpoint'],
                                               werkzeug.url_encode(params))
        return providers


class OAuthController(http.Controller):

    @http.route('/auth_oauth/microsoft/signin',
                type='http',
                auth='none',
                csrf=False)
    @fragment_to_query_string
    def microsoft_signin(self, **kw):
        pool = request.env
        root_url = request.env['ir.config_parameter'].sudo().get_param(
            'web.base.url') + '/'
        oauth_provider_rec =\
            pool['ir.model.data'].sudo().get_object_reference(
                'external_login',
                'provider_microsoft')[1]
        provider = \
            pool['auth.oauth.provider'].sudo().browse(oauth_provider_rec)
        authorization_data = \
            pool['auth.oauth.provider'].sudo().oauth_token(
                'authorization_code',
                provider,
                kw.get('code'),
                refresh_token=None)
        access_token = authorization_data.get('access_token')
        refresh_token = authorization_data.get('refresh_token')
        user_id = False
        mail = False
        displayname = False
        try:
            conn = httplib.HTTPSConnection(provider.data_endpoint)
            conn.request("GET", "/v1.0/me", "", {
                'Authorization': access_token,
                'Accept': 'application/json'
            })
            response = conn.getresponse()
            data = simplejson.loads(response.read())
            displayname = data.get('displayName')
            mail = data.get('userPrincipalName')
            user_id = data.get('id')
            conn.close()
        except Exception as e:
            print(e)
        try:
            credentials = pool['res.users'].sudo().microsoft_auth_oauth(
                provider.id, {
                    'access_token': access_token,
                    'user_id': user_id,
                    'email': mail,
                    'name': displayname,
                    'microsoft_refresh_token': refresh_token
                })
            request.cr.commit()
            return login_and_redirect(*credentials,
                                      redirect_url=root_url + 'web?')
        except AttributeError:
                _logger.error(
                    "auth_signup not installed on"
                    " database %s: oauth sign up cancelled." % (
                        request.cr.dbname))
                url = "/web/login?oauth_error=1"
        except odoo.exceptions.AccessDenied:
                _logger.info('OAuth2: access denied,'
                             ' redirect to main page in case a valid'
                             ' session exists, without setting cookies')
                url = "/web/login?oauth_error=3"
                redirect = werkzeug.utils.redirect(url, 303)
                redirect.autocorrect_location_header = False
                return redirect
        except Exception as e:
            _logger.exception("OAuth2: %s" % str(e))
            url = "/web/login?oauth_error=2"
        return set_cookie_and_redirect(root_url + url)

    @http.route('/auth_oauth/wadmin/signin',
                type='http',
                auth='none',
                csrf=False)
    @fragment_to_query_string
    def wadmin_signin(self, **kw):
        pool = request.env
        root_url = request.env['ir.config_parameter'].sudo().get_param(
            'web.base.url') + '/'
        oauth_provider_rec =\
            pool['ir.model.data'].sudo().get_object_reference(
                'external_login',
                'provider_wsuite')[1]
        provider = \
            pool['auth.oauth.provider'].sudo().browse(oauth_provider_rec)
        authorization_data = \
            pool['auth.oauth.provider'].sudo().wadmin_oauth_token(
                'authorization_code',
                provider,
                kw.get('code'),
                refresh_token=None)
        print("authorization_data", authorization_data)
        access_token = authorization_data.get('access_token')
        refresh_token = authorization_data.get('refresh_token')
        user_id = False
        mail = False
        displayname = False
        try:
            headers = {'Authorization': 'Bearer ' + access_token,
                       'Accept': 'application/json'}
            response = requests.request('GET', provider.user_access_url,
                                        headers=headers)
            _logger.info("Response.text: %s", response.text)
            data = simplejson.loads(response.text)
            displayname = data.get('name') + data.get('middle_name')
            mail = data.get('email')
            user_id = data.get('sub')
        except Exception as e:
            print(e)
        try:
            credentials = pool['res.users'].sudo().microsoft_auth_oauth(
                provider.id, {
                    'access_token': access_token,
                    'user_id': user_id,
                    'email': mail,
                    'name': displayname,
                    'wadmin_refresh_token': refresh_token
                })
            request.cr.commit()
            return login_and_redirect(*credentials,
                                      redirect_url=root_url + 'web?')
        except AttributeError:
                _logger.error(
                    "auth_signup not installed on"
                    " database %s: oauth sign up cancelled." % (
                        request.cr.dbname))
                url = "/web/login?oauth_error=1"
        except odoo.exceptions.AccessDenied:
                _logger.info('OAuth2: access denied,'
                             ' redirect to main page in case a valid'
                             ' session exists, without setting cookies')
                url = "/web/login?oauth_error=3"
                redirect = werkzeug.utils.redirect(url, 303)
                redirect.autocorrect_location_header = False
                return redirect
        except Exception as e:
            _logger.exception("OAuth2: %s" % str(e))
            url = "/web/login?oauth_error=2"
        return set_cookie_and_redirect(root_url + url)


class Session(ses):

    @http.route('/web/session/authenticate', type='json', auth="none")
    def authenticate(self, db, login, password, base_location=None):
        if not login and not password:
            access_token = request.httprequest.headers.get('access_token')
            slug = request.httprequest.headers.get('partner')
            url_env = request.httprequest.headers.get('environment')
            try:
                if not access_token:
                    info = "Missing access token in request header!"
                    error = 'access_token Not Found'
                    _logger.error(info)
                    return werkzeug.wrappers.Response(
                        status=400,
                        content_type='application/json; charset=utf-8',
                        response=json.dumps({
                            'error': error,
                            'error_description': info,
                        }),
                    )
                if not slug:
                    info = "Missing partner(slug) in request header!"
                    error = 'partner(slug) Not Found'
                    _logger.error(info)
                    return werkzeug.wrappers.Response(
                        status=400,
                        content_type='application/json; charset=utf-8',
                        response=json.dumps({
                            'error': error,
                            'error_description': info,
                        }),
                    )
                if not url_env:
                    info = "Missing environment in request header!"
                    error = 'environment Not Found'
                    _logger.error(info)
                    return werkzeug.wrappers.Response(
                        status=400,
                        content_type='application/json; charset=utf-8',
                        response=json.dumps({
                            'error': error,
                            'error_description': info,
                        }),
                    )
#                 JWT_SECRET = """-----BEGIN PUBLIC KEY-----
# MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAnP/lXv5JMqnsHxleNjsZ
# ImlLx+kloVJ4yoZFavGIkKZ2OsC+mk/4c5C/BUnyHo/ANyP6wIraexuJ1qTWdZcA
# HmXtJlZoWGlKB6A4ZER3Vha0EQy+j7ZjY+joR+QxZPImr4h5eSlquGbmNOAwUVn8
# LJr2yQKRcdSEZfhK7voIeYJvPW4l4luL8pCQSQnxez+/rQuk8zclnLVcNJJgbm13
# 88Yn2vN4wfMRRgSbdNLyT6K2yIC7HcGcprZq3icJ71BdZde2AOvzjFe0YFGsRrWj
# QWnp6CLR+4llqbZ9xm3Etuqvw9/5MMw39G/XKJufYsYrx65IjixoBFn/j/Twf1Rw
# xwIDAQAB
# -----END PUBLIC KEY-----"""
                JWT_SECRET = request.env['ir.config_parameter'].sudo().get_param('public_key')
                db_name = 'werp_' + slug
                _logger.info(" db_name : %s", db_name)
                db_list = odoo.service.db.list_dbs(True)
                final_db_list = []
                for db in db_list:
                    if not http.db_filter([db]):
                        continue
                    final_db_list.append(db)
                print("==final_db_list==", final_db_list)
                if db_name not in final_db_list:
                    _logger.error("Database invalid!")
                    info = "Database (%s) not exists!" % db_name
                    error = "Database (%s) not exists!" % db_name
                    _logger.error(info)
                    return werkzeug.wrappers.Response(
                        status=400,
                        content_type='application/json; charset=utf-8',
                        headers=[('Cache-Control', 'no-store'),
                                 ('Pragma', 'no-cache')],
                        response=json.dumps({
                            'error': error,
                            'error_descrip': info,
                        }),
                    )
                root_url = request.env['ir.config_parameter'].sudo().get_param(
                    'web.base.url') + '/'
                decode_token = jwt.decode(access_token, verify=False)
                _logger.info(" decode_token : %s", decode_token)

                # Currently check for admin users
                # users = request.env['res.users'].sudo().search([
                #     ("login", "=", 'admin')
                # ], limit=1)

                # For Dynamic user from Cognito Token
                user = decode_token.get('username')
                request.session.db = db_name
                users = request.env['res.users'].sudo().search([
                    ("login", "=", user)
                ], limit=1)
                _logger.info(" user : %s", user)
                if not users:
                    raise AccessDenied()

                # Static DB
                # credentials = 'werpdev_quadi', users.login, access_token

                # For Dynamic DB from Cognito Token
                credentials = db_name, users.login, access_token

                # users.sudo().write({'oauth_access_token': access_token})
                # request.cr.commit()
                login_and_redirect(*credentials, redirect_url=root_url + 'web?')
                return request.env['ir.http'].session_info()

            except jwt.exceptions.InvalidTokenError as e:
                request._cr.rollback()
                _logger.error("Token is expired or invalid!")
                info = "Token is expired or invalid!!"
                error = 'token_expired_or_invalid'
                _logger.error(info)
                return werkzeug.wrappers.Response(
                    status=400,
                    content_type='application/json; charset=utf-8',
                    headers=[('Cache-Control', 'no-store'),
                             ('Pragma', 'no-cache')],
                    response=json.dumps({
                        'error': error,
                        'error_descrip': info,
                    }),
                )
            except jwt.ExpiredSignatureError as e:
                request._cr.rollback()
                _logger.error("Invalid Signature %s" % e)
                return werkzeug.wrappers.Response(
                    status=400,
                    content_type='application/json; charset=utf-8',
                    response=json.dumps({
                        'error': 'expired_signature',
                        'error_description': "Invalid Signature %s" % e,
                    }),
                )
        request.session.authenticate(db, login, password)
        return request.env['ir.http'].session_info()
