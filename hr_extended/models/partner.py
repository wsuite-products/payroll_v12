# Copyright 2019-TODAY WSuite Products <wsuite-products@destiny.ws>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError
import odoo
import logging
from odoo import http
_logger = logging.getLogger(__name__)


class Partner(models.Model):
    """Extend Partner."""

    _inherit = 'res.partner'

    is_found_layoffs = fields.Boolean(string='Found Layoffs')
    is_compensation_box = fields.Boolean(string='Compensation Box')
    is_eps = fields.Boolean(string='EPS')
    is_unemployee_fund = fields.Boolean(string='Unemployee Fund')
    is_arl = fields.Boolean(string='ARL')
    is_prepaid_medicine = fields.Boolean(string='Prepaid Medicine')
    is_afc = fields.Boolean(string='AFS')
    is_voluntary_contribution = fields.Boolean(string='Voluntary Contribution')
    is_afp = fields.Boolean(string='AFP')
    file_cv = fields.Binary(string='File', attachment=True)
    attachment_url = fields.Char("URL")
    file_cv_name = fields.Char(string='File CV Name')
    file_cv_size = fields.Char(string='File CV Size')
    linked_return_url = fields.Char(string='Linked Return Url')
    mobile_country_code = fields.Char(string='Mobile Country Code')
    phone_country_code = fields.Char(string='Phone Country Code')
    l10n_co_document_type = fields.Selection(
        selection_add=[
            ('NIT', 'N.I.T.'),
            ('external_NIT', 'Nit Extranjería'),
            ('external_society_without_NIT',
             'Sociedad extranjera sin N.I.T. En Colombia'),
            ('trust', 'Fideicomiso'),
            ('natural_person_NIT', 'Nit persona natural')])
    function_id = fields.Many2one('hr.job', 'Job Position')
    client_reference = fields.Integer('Client Reference')

    @api.model
    def create(self, vals):
        # This code is for resolved the Incorrect padding issues.
        attachment_url = ''
        if vals.get('attachment_url'):
            attachment_url = vals['attachment_url']
            vals.pop('attachment_url')
        linked_return_url = ''
        if vals.get('linked_return_url'):
            linked_return_url = vals['linked_return_url']
            vals.pop('linked_return_url')
        res = super(Partner, self).create(vals)
        if attachment_url:
            res.attachment_url = attachment_url
        if linked_return_url:
            res.linked_return_url = linked_return_url
        return res


class ResUsers(models.Model):
    """Extend Users."""

    _inherit = "res.users"

    you_websocket_token = fields.Char('You Websocket Token')
    birthdate = fields.Date('Date of birth')
    wp_api_token = fields.Char('W-Project API Token')
    cognito_sub = fields.Char('Cognito Sub')

    @api.multi
    def active_or_inactive_user(self, flag, email):
        db_list = odoo.service.db.list_dbs(True)
        current_cr = self._cr
        _logger.info(" db_list : %s", db_list)
        for db in db_list:
            if not http.db_filter([db]):
                continue
            _logger.info(" db : %s", db)
            try:
                if db == current_cr.dbname:
                    continue
                try:
                    new_db = odoo.sql_db.db_connect(db)
                    with new_db.cursor() as cr:
                        cr.execute('SELECT id from res_company where generate_process_in_other_db=True')
                        result = cr.fetchone()
                        if not result:
                            _logger.info(" Fetch : %s", cr.fetchone())
                            continue
                        cr.execute(
                            'UPDATE res_users SET active=%s WHERE login=%s', (
                                flag, email))
                except Exception as e:
                    raise UserError(_('Record update issues') % tools.ustr(e))
                odoo.sql_db.close_db(db)
            except:
                raise UserError(_(
                    'There seems a problem in the database:- ' + str(db)))

    @api.multi
    def write(self, vals):
        active = vals.get('active')
        if active is False:
            email = vals.get('login') or self.login
            if email:
                self.active_or_inactive_user(False, email)
        elif active is True:
            email = vals.get('login') or self.login
            if email:
                self.active_or_inactive_user(True, email)
        return super(ResUsers, self).write(vals)
