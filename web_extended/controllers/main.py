# Copyright 2020-TODAY Anand Kansagra <anandkansagra@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import werkzeug
import jwt

from odoo.addons.web.controllers.main \
    import Home
from odoo.addons.web.controllers.main \
    import Database
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import login_and_redirect


class Home(Home):

    @http.route('/', type='http', auth="none")
    def index(self, s_action=None, db=None, **kw):
        if request.httprequest.url_root:
            if 'localhost' in request.httprequest.url_root:
                return werkzeug.utils.redirect(
                    'https://development-admin.wsuite.com', 303)
            if 'https://development-wsuiteerp.wsuite.com' in\
                    request.httprequest.url_root:
                return werkzeug.utils.redirect(
                    'https://development-admin.wsuite.com', 303)
            if 'https://stage-wsuiteerp.wsuite.com' in\
                    request.httprequest.url_root:
                return werkzeug.utils.redirect(
                    'https://staging-admin.wsuite.com', 303)
            if 'https://wsuiteerp.wsuite.com' in request.httprequest.url_root:
                return werkzeug.utils.redirect(
                    'https://admin.wsuite.com', 303)
            if 'https://erp.wsuite.com' in request.httprequest.url_root:
                return werkzeug.utils.redirect(
                    'https://admin.wsuite.com', 303)
        return http.local_redirect(
            '/web', query=request.params, keep_hash=True)

    @http.route('/web/autologin/wadmin', type='http',
                auth="none", sitemap=False)
    def web_auto_login_wadmin(self, redirect=None, **kw):
        """Auto login for switch the database."""
        if kw.get('partner') and kw.get('access_token') and\
                request.httprequest.url_root:
            decode_token = jwt.decode(kw.get('access_token'), verify=False)
            db_name = 'werp_' + kw.get('partner')
            user = decode_token.get('email')
            credentials = db_name, user, kw.get('access_token')
            request.params['login_success'] = True
            resp = login_and_redirect(
                *credentials,
                redirect_url=request.httprequest.url_root + 'web?')
            return resp


class Database(Database):

    @http.route('/web/database/directaccesswerp/selector', type='http', auth="none")
    def selector_directaccesswerp(self, **kw):
        request._cr = None
        return self._render_template(manage=False)

    @http.route('/web/database/directaccesswerp/manager', type='http', auth="none")
    def manager_directaccesswerp(self, **kw):
        request._cr = None
        return self._render_template()

    @http.route('/web/session/logout', type='http', auth="none")
    def logout(self, redirect='/web'):
        request.session.logout(keep_db=True)
        if request.httprequest.url_root:
            if 'localhost' in request.httprequest.url_root:
                return werkzeug.utils.redirect(
                    'https://development-admin.wsuite.com', 303)
            if 'https://development-wsuiteerp.wsuite.com' in\
                    request.httprequest.url_root:
                return werkzeug.utils.redirect(
                    'https://development-admin.wsuite.com', 303)
            if 'https://stage-wsuiteerp.wsuite.com' in\
                    request.httprequest.url_root:
                return werkzeug.utils.redirect(
                    'https://staging-admin.wsuite.com', 303)
            if 'https://wsuiteerp.wsuite.com' in request.httprequest.url_root:
                return werkzeug.utils.redirect(
                    'https://admin.wsuite.com', 303)
            if 'https://erp.wsuite.com' in request.httprequest.url_root:
                return werkzeug.utils.redirect(
                    'https://admin.wsuite.com', 303)
        return http.local_redirect(
            '/web', query=request.params, keep_hash=True)

    @http.route('/web/database/selector', type='http', auth="none")
    def selector(self, **kw):
        request._cr = None
        if request.httprequest.url_root:
            if 'localhost' in request.httprequest.url_root:
                return werkzeug.utils.redirect(
                    'https://development-admin.wsuite.com', 303)
            if 'https://development-wsuiteerp.wsuite.com' in\
                    request.httprequest.url_root:
                return werkzeug.utils.redirect(
                    'https://development-admin.wsuite.com', 303)
            if 'https://stage-wsuiteerp.wsuite.com' in\
                    request.httprequest.url_root:
                return werkzeug.utils.redirect(
                    'https://staging-admin.wsuite.com', 303)
            if 'https://wsuiteerp.wsuite.com' in request.httprequest.url_root:
                return werkzeug.utils.redirect(
                    'https://admin.wsuite.com', 303)
            if 'https://erp.wsuite.com' in request.httprequest.url_root:
                return werkzeug.utils.redirect(
                    'https://admin.wsuite.com', 303)
        return http.local_redirect(
            '/web', query=request.params, keep_hash=True)

    @http.route('/web/database/manager', type='http', auth="none")
    def manager(self, **kw):
        request._cr = None
        if request.httprequest.url_root:
            if 'localhost' in request.httprequest.url_root:
                return werkzeug.utils.redirect(
                    'https://development-admin.wsuite.com', 303)
            if 'https://development-wsuiteerp.wsuite.com' in\
                    request.httprequest.url_root:
                return werkzeug.utils.redirect(
                    'https://development-admin.wsuite.com', 303)
            if 'https://stage-wsuiteerp.wsuite.com' in\
                    request.httprequest.url_root:
                return werkzeug.utils.redirect(
                    'https://staging-admin.wsuite.com', 303)
            if 'https://wsuiteerp.wsuite.com' in request.httprequest.url_root:
                return werkzeug.utils.redirect(
                    'https://admin.wsuite.com', 303)
            if 'https://erp.wsuite.com' in request.httprequest.url_root:
                return werkzeug.utils.redirect(
                    'https://admin.wsuite.com', 303)
        return http.local_redirect(
            '/web', query=request.params, keep_hash=True)
