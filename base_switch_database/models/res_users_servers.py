# Copyright 2019-TODAY Anand Kansagra <anandkansagra@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models, tools, http
import logging
from odoo.http import request
from odoo.service import security
import werkzeug.contrib.sessions
from odoo.exceptions import AccessDenied
_logger = logging.getLogger(__name__)


class ResUsersServers(models.Model):
    """Add the information of the User Server."""

    _name = "res.users.servers"
    _rec_name = "company_id"
    _description = "User Server"

    @api.multi
    @api.depends('server_id.server_url', 'server_id.server_port',
                 'server_id.server_db', 'server_id.login',
                 'server_id.password', 'server_id.is_microsoft_login')
    def _compute_switch_database_url(self):
        for rec in self:
            if rec.server_id and not rec.server_id.is_microsoft_login and \
                    not rec.server_id.is_w_admin:
                rec.switch_database_url = rec.server_id.server_url + ':' +\
                    str(rec.server_id.server_port) + '/web/autologin?db=' +\
                    rec.server_id.server_db + '&login=' +\
                    rec.server_id.login + '&password=' + rec.server_id.password
            if rec.server_id and \
                    (rec.server_id.is_microsoft_login or
                     rec.server_id.is_w_admin):
                rec.switch_database_url = rec.server_id.server_url + ':' +\
                    str(rec.server_id.server_port) + '/web?db=' +\
                    rec.server_id.server_db

    server_id = fields.Many2one(
        'base.synchro.server', 'Server')
    user_id = fields.Many2one(
        'res.users', 'User')
    company_id = fields.Many2one(
        'res.partner',
        related="server_id.company_id",
        string="Company")
    image_company = fields.Binary(
        related="server_id.company_id.image",
        string="Company Image")
    switch_database_url = fields.Char(
        'Switch Database URL',
        compute="_compute_switch_database_url")
    is_microsoft_login = fields.Boolean(
        'Microsoft Login', related="server_id.is_microsoft_login")
    is_w_admin = fields.Boolean(
        'Microsoft Login', related="server_id.is_w_admin")


class Users(models.Model):
    _inherit = "res.users"

    @api.model
    @tools.ormcache('self._uid')
    def context_get(self):
        # Override to checking user on other
        # database using Switch Database
        user = self.env.user
        # determine field names to read
        name_to_key = {
            name: name[8:] if name.startswith('context_') else name
            for name in self._fields
            if name.startswith('context_') or name in ('lang', 'tz')
        }
        # use read() to not read other fields: this must work while modifying
        # the schema of models res.users or res.partner
        list_data = user.read(list(name_to_key), load=False)
        if list_data:
            values = list_data[0]
        else:
            values = {'id': user.id, 'lang': 'en_US', 'tz': 'America/Bogota'}
        return {
            key: values[name]
            for name, key in name_to_key.items()
        }


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _authenticate(cls, auth_method='user'):
        try:
            if request.session.uid:
                try:
                    if not request.session.session_token:
                        session_token = security.compute_session_token(
                            request.session, request.env)
                        request.session.session_token = session_token
                    request.session.check_security()
                    # what if error in security.check()
                    #   -> res_users.check()
                    #   -> res_users._check_credentials()
                except (AccessDenied, http.SessionExpiredException):
                    # All other exceptions mean undetermined
                    # status (e.g. connection pool full),
                    # let them bubble up
                    request.session.logout(keep_db=True)
            if request.uid is None:
                getattr(cls, "_auth_method_%s" % auth_method)()
        except (AccessDenied, http.SessionExpiredException,
                werkzeug.exceptions.HTTPException):
            raise
        except Exception:
            _logger.info("Exception during request "
                         "Authentication.", exc_info=True)
            raise AccessDenied()
        return auth_method
