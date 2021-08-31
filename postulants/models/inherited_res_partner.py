# Copyright 2019-TODAY Anand Kansagra <anandkansagra@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import oauth2
import lxml.html
import mechanize
import linkedin
import re
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class Partner(models.Model):
    """Added the postulant details in the partner."""

    _inherit = "res.partner"

    postulant = fields.Boolean(track_visibility='always')
    first_name = fields.Char(string='First Name')
    second_name = fields.Char(string='Second Name')
    surname = fields.Char(string='Surname')
    second_surname = fields.Char(string='Second Surname')
    hr_applicant_ids = fields.One2many('hr.applicant', 'partner_id')
    referred_by_partner_id = fields.Many2one(
        'res.partner', string='Referred By')
    referred_channel_id = fields.Many2one(
        'hr.referred.channel', string='Referred Channel')
    link = fields.Char("Applicant's CV Link")
    state_selection = fields.Selection([
        ('eligible', 'Eligible'),
        ('not_elig0ible', 'Not Eligible'),
        ('in_process', 'In Process'),
        ('hired', 'Hired'),
    ], string='State Selection', default='eligible',
        copy=False)
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ])
    hr_cv_employee_id = fields.Many2one(
        'hr.cv.employee', string='Curriculum Vitae')

    @api.onchange('first_name', 'second_name', 'surname', 'second_surname')
    def onchange_name(self):
        name = "{0} {1} {2} {3}".format(
            self.surname or '',
            self.second_surname or '',
            self.first_name or '',
            self.second_name or '')
        self.name = re.sub("\s\s+", " ", name)

    @api.onchange('postulant')
    def _onchange_postulant(self):
        self.state_selection = ''
        if self.postulant:
            self.state_selection = 'eligible'

    @api.multi
    def sync(self):
        """Sync Data from LinkedIn."""
        linkedin_con_obj = self.env['linkedin.data.configuration'].search(
            [], limit=1)
        if not linkedin_con_obj:
            raise ValidationError(_(
                'Please configure the LinkedIn under'
                ' Employee -> Configuration -> LinkedIn Data'))
        else:
            try:
                consumer = oauth2.Consumer(
                    linkedin_con_obj.api_key, linkedin_con_obj.secret_key)
                client = oauth2.Client(consumer)
                request_token_url =\
                    'https://api.linkedin.com/uas/oauth/requestToken'
                response, content = client.request(
                    request_token_url, method='POST')
                token = str(content)
                start = 'oauth_token='
                end = '&oauth_token_secret='
                end_final = '&oauth_callback_confirmed='
                auth_token = (token.split(start))[1].split(end)[0]
                auth_token_secret = (token.split(end))[1].split(end_final)[0]
                authorize_url = 'https://api.linkedin.com/uas/oauth/authorize'
                redirect_url = '%s?oauth_token=%s' % (
                    authorize_url, auth_token)
                br = mechanize.Browser()
                br.set_cookiejar(mechanize.CookieJar())
                br.set_handle_redirect(True)
                br.set_handle_robots(False)
                br.open(redirect_url)
                br.select_form(nr=0)
                br.form['session_key'] = linkedin_con_obj.user
                br.form['session_password'] = linkedin_con_obj.password
                br.submit()
                html = br.response().read()
                tree = lxml.html.fromstring(html)
                oauth_verifier = tree.xpath(
                    './/div[@class="access-code"]')[0].text_content()
                token = oauth2.Token(auth_token, auth_token_secret)
                token.set_verifier(oauth_verifier)
                access_token_url =\
                    'https://api.linkedin.com/uas/oauth/accessToken'
                client = oauth2.Client(consumer, token)
                response, content = client.request(access_token_url, 'POST')
                token = str(content)
                start = 'oauth_token='
                end = '&oauth_token_secret='
                end_final = '&oauth_expires_in='
                auth_token = (token.split(start))[1].split(end)[0]
                auth_token_secret = (token.split(end))[1].split(end_final)[0]
                li_permissions = ['r_fullprofile']
                authentication = linkedin.LinkedInDeveloperAuthentication(
                    linkedin_con_obj.api_key, linkedin_con_obj.secret_key,
                    auth_token, auth_token_secret,
                    linkedin_con_obj.return_url, li_permissions)
                application = linkedin.LinkedInApplication(authentication)
                partner_rec_dict = {'postulant': True}
                if not self.link:
                    application_data = application.get_profile(
                        selectors=[
                            'id', 'firstName', 'lastName', 'headline',
                            'location', 'summary', 'positions'])
                    name = ''
                    if application_data.get('firstName'):
                        name = application_data.get('firstName')
                    if application_data.get(
                            'lastName') and application_data.get('firstName'):
                        name += ' ' + application_data.get('lastName')
                    if name:
                        partner_rec_dict.update({'name': name})
                    if application_data.get('headline'):
                        partner_rec_dict.update({
                            'function': application_data.get('headline')})
                    if application_data.get('location'):
                        if application_data.get('location').get('country') and\
                                application_data.get('location').get(
                                    'country').get('code'):
                            country = self.env['res.country'].search([
                                ('code', '=', application_data.get(
                                    'location').get('country').get(
                                    'code').upper())],
                                limit=1)
                            if country:
                                partner_rec_dict.update(
                                    {'country_id': country.id})
                        if application_data.get('location').get('name'):
                            city = application_data.get('location').get('name')
                            partner_rec_dict.update(
                                {'city': city.split(',', 1)[0]})
                    if partner_rec_dict:
                        if self.env['res.partner'].search([
                                ('name', '=', partner_rec_dict.get('name'))]):
                            partner_rec = self.env['res.partner'].search([
                                ('name', '=', partner_rec_dict.get('name'))],
                                limit=1)
                        else:
                            partner_rec = self.env['res.partner'].create(
                                partner_rec_dict)
                    if partner_rec:
                        self.update({'partner_id': partner_rec.id,
                                     'partner_name': name})
                else:
                    application_data = application.get_profile(
                        member_url=self.link,
                        selectors=[
                            'id', 'firstName', 'lastName', 'headline',
                            'location', 'summary', 'positions'])
                    name = ''
                    if application_data.get('firstName'):
                        name = application_data.get('firstName')
                    if application_data.get(
                            'lastName') and application_data.get('firstName'):
                        name += ' ' + application_data.get('lastName')
                    if name:
                        partner_rec_dict.update({'name': name})
                    if application_data.get('headline'):
                        partner_rec_dict.update({
                            'function': application_data.get('headline')})
                    if application_data.get('location'):
                        if application_data.get('location').get('country') and\
                                application_data.get('location').get(
                                    'country').get('code'):
                            country = self.env['res.country'].search([
                                ('code', '=', application_data.get(
                                    'location').get('country').get(
                                    'code').upper())],
                                limit=1)
                            if country:
                                partner_rec_dict.update(
                                    {'country_id': country.id})
                        if application_data.get('location').get('name'):
                            city = application_data.get('location').get('name')
                            partner_rec_dict.update(
                                {'city': city.split(',', 1)[0]})
                    if partner_rec_dict:
                        if self.env['res.partner'].search([
                                ('name', '=', partner_rec_dict.get('name'))]):
                            partner_rec = self.env['res.partner'].search([
                                ('name', '=', partner_rec_dict.get('name'))],
                                limit=1)
                        else:
                            partner_rec = self.env['res.partner'].create(
                                partner_rec_dict)
                    if partner_rec:
                        self.update({'partner_id': partner_rec.id,
                                     'partner_name': name})
            except:
                raise ValidationError(_(
                    'There seems a problem in fetch data from the LinkedIn'))
