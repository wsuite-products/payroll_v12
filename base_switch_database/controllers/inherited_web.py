# Copyright 2019-TODAY Anand Kansagra <anandkansagra@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mechanize
import lxml.html
import jwt
from odoo import http, _
from odoo.http import request
from odoo.addons.web.controllers.main import Home
from odoo.exceptions import ValidationError
from odoo.addons.web.controllers.main import  login_and_redirect
import logging
_logger = logging.getLogger(__name__)


class Home(Home):
    """Auto login for switch the database."""

    @http.route('/web/autologin', type='http', auth="none", sitemap=False)
    def web_auto_login(self, redirect='/web', **kw):
        """Auto login for switch the database."""
        try:
            if not kw.get('db') and kw.get('id'):
                bss_id = request.env['base.synchro.server'].sudo().browse(int(kw.get('id')))
                uid = request.session.authenticate(bss_id.server_db, bss_id.login, bss_id.password)
            elif kw.get('partner') and kw.get('access_token'):
                root_url = request.env['ir.config_parameter'].sudo().get_param(
                    'web.base.url') + '/'
                decode_token = jwt.decode(kw.get('access_token'), verify=False)
                db_name = 'werp_' + kw.get('partner')
                _logger.info(" decode_token : %s", decode_token)
                user = decode_token.get('email')
                uid = request.env['res.users'].sudo().search([
                    ("login", "=", user)], limit=1)
                if not uid:
                    user = decode_token.get('username')
                    uid = request.env['res.users'].sudo().search([
                        ("login", "=", user)], limit=1)
                if not uid:
                    user = decode_token.get('cognito:username')                    
                    uid = request.env['res.users'].sudo().search([
                        ("login", "=", user)], limit=1)
                _logger.info(" user : %s", user, uid)
                credentials = db_name, uid.login, kw.get('access_token')
                login_and_redirect(*credentials, redirect_url=root_url + 'web?')
            else:
                uid = request.session.authenticate(kw.get('db'), kw.get('login'), kw.get('password'))
            request.params['login_success'] = True
            return http.redirect_with_hash(
                self._login_redirect(uid, redirect=redirect))

        except Exception as e:
            _logger.exception(" \nException \"%s\"", str(e))
            raise ValidationError(_(
                'Please check credential or check base_switch_database module'
                ' is installed in the switcher instance.'))

    @http.route('/microsoftlogin', type='json', auth='none')
    def microsoftlogin(self, url_database, provider=None):
        """Get Microsoft URL from another database"""
        if url_database:
            br = mechanize.Browser()
            br.set_cookiejar(mechanize.CookieJar())
            br.set_handle_redirect(True)
            br.set_handle_robots(False)
            br.open(url_database)
            html = br.response().read()
            tree = lxml.html.fromstring(html)
            oauth_verifiers = tree.xpath(
                './/div[@class="o_auth_oauth_providers list-group mt-1 mb-1 text-left"]')
            for oauth_verifier in oauth_verifiers[0].getchildren():
                if provider in oauth_verifier.text_content(
                )and oauth_verifier.get('href'):
                    return oauth_verifier.get('href')
