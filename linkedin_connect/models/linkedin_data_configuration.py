# Copyright 2019-TODAY Anand Kansagra <anandkansagra@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class LinkedinDataConfiguration(models.Model):
    """Added the LinkedIn Data Configuration object."""

    _name = "linkedin.data.configuration"
    _rec_name = "user"
    _description = 'LinkedIn Configuration Data'

    api_key = fields.Char('API Key')
    secret_key = fields.Char('Secret Key')
    user = fields.Char('Username')
    password = fields.Char('Password')
    return_url = fields.Char('Return URL')
