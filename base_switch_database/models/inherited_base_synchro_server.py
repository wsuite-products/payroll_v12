# Copyright 2019-TODAY Anand Kansagra <anandkansagra@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class BaseSynchroServer(models.Model):
    """Added Company in the base synchro server."""

    _inherit = "base.synchro.server"

    company_id = fields.Many2one(
        'res.partner', 'Company', domain=[('company', '=', True)])
    is_microsoft_login = fields.Boolean('Microsoft Login')
    is_w_admin = fields.Boolean('W-admin Login')
