# Copyright 2019-TODAY Anand Kansagra <anandkansagra@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import oauth2
import lxml.html
import mechanize
import linkedin

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrApplicant(models.Model):
    """Added the reference field of the partner for One2many."""

    _inherit = "hr.applicant"

    partner_id = fields.Many2one('res.partner')
    is_linkedin = fields.Boolean('LinkedIn')
    linked_api_key = fields.Char('LinkedIn API Key')
    linked_secret_key = fields.Char('LinkedIn Secret Key')
    linked_user = fields.Char('LinkedIn User')
    linked_password = fields.Char('LinkedIn Password')
    linked_return_url = fields.Char('LinkedIn Return URL')
    reference = fields.Many2one('hr.referred.channel',
                                related='partner_id.referred_channel_id',
                                store=True)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """Onchange on Partner for Applicant Name."""
        if self.partner_id:
            self.partner_name = self.partner_id.name

    @api.multi
    def sync_linkedin(self):
        """Sync Data from LinkedIn."""
        try:
            consumer = oauth2.Consumer(
                self.linked_api_key, self.linked_secret_key)
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
            redirect_url = '%s?oauth_token=%s' % (authorize_url, auth_token)
            br = mechanize.Browser()
            br.set_cookiejar(mechanize.CookieJar())
            br.set_handle_redirect(True)
            br.set_handle_robots(False)
            br.open(redirect_url)
            br.select_form(nr=0)
            br.form['session_key'] = self.linked_user
            br.form['session_password'] = self.linked_password
            br.submit()
            html = br.response().read()
            tree = lxml.html.fromstring(html)
            oauth_verifier = tree.xpath(
                './/div[@class="access-code"]')[0].text_content()
            token = oauth2.Token(auth_token, auth_token_secret)
            token.set_verifier(oauth_verifier)
            access_token_url = 'https://api.linkedin.com/uas/oauth/accessToken'
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
                self.linked_api_key, self.linked_secret_key,
                auth_token, auth_token_secret,
                self.linked_return_url, li_permissions)
            application = linkedin.LinkedInApplication(authentication)
            application_data = application.get_profile(
                selectors=['id', 'first-name', 'last-name', 'location',
                           'distance', 'num-connections', 'skills',
                           'educations'])
            name = ''
            if application_data.get('firstName'):
                name = application_data.get('firstName')
            if application_data.get('lastName') and application_data.get(
                    'firstName'):
                name += ' ' + application_data.get('lastName')
            if name:
                self.partner_name = name
        except:
            raise ValidationError(_(
                'There seems a problem in fetch data from the LinkedIn'))

    @api.multi
    def create_employee_from_applicant(self):
        """Add Curriculum Vitae information."""
        res = super(HrApplicant, self).create_employee_from_applicant()
        hr_cv_employee_rec = self.env['hr.cv.employee'].search([
            ('partner_id', '=', self.partner_id.id)], limit=1)
        if res.get('res_id', '') and hr_cv_employee_rec:
            employee = self.env['hr.employee'].browse(res.get('res_id', ''))
            if hr_cv_employee_rec.hobbies_ids:
                for hobby in hr_cv_employee_rec.hobbies_ids:
                    hobby.copy(default={'employee_id': employee.id,
                                        'hr_cv_employee_id': ''})
            if hr_cv_employee_rec.sport_ids:
                for sport in hr_cv_employee_rec.sport_ids:
                    sport.copy(default={'employee_id': employee.id,
                                        'hr_cv_employee_id': ''})
            if hr_cv_employee_rec.language_ids:
                for language in hr_cv_employee_rec.language_ids:
                    language.copy(default={'employee_id': employee.id,
                                           'hr_cv_employee_id': ''})
            if hr_cv_employee_rec.holding_ids:
                for holding in hr_cv_employee_rec.holding_ids:
                    holding.copy(default={'employee_id': employee.id,
                                          'hr_cv_employee_id': ''})
            if hr_cv_employee_rec.family_group_ids:
                for family_group in hr_cv_employee_rec.family_group_ids:
                    family_group.copy(default={'employee_id': employee.id,
                                               'hr_cv_employee_id': ''})
            if hr_cv_employee_rec.laboral_experience_ids:
                for laboral_experience in\
                        hr_cv_employee_rec.laboral_experience_ids:
                    laboral_experience.copy(
                        default={'employee_id': employee.id,
                                 'hr_cv_employee_id': ''})
            if hr_cv_employee_rec.academic_studies_ids:
                for academic_studies in\
                        hr_cv_employee_rec.academic_studies_ids:
                    academic_studies.copy(default={'employee_id': employee.id,
                                                   'hr_cv_employee_id': ''})
            if hr_cv_employee_rec.animal_pets_ids:
                for animal_pets in hr_cv_employee_rec.animal_pets_ids:
                    animal_pets.copy(default={'employee_id': employee.id,
                                              'hr_cv_employee_id': ''})
            if hr_cv_employee_rec.personal_employee_ids:
                for personal_employee in\
                        hr_cv_employee_rec.personal_employee_ids:
                    personal_employee.copy(default={'employee_id': employee.id,
                                                    'hr_cv_employee_id': ''})
        return res
