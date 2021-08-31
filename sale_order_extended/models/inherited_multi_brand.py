# Copyright 2019-TODAY Anand Kansagra <anandkansagra@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class MultiBrand(models.Model):
    """Extend Multi Brand."""

    _inherit = 'multi.brand'

    partner_id = fields.Many2one('res.partner')
    users_ids = fields.Many2many('res.users', string='Users')
    service_agreement = fields.Float('Service Agreement')
