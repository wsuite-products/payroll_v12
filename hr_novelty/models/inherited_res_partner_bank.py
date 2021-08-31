# Copyright 2020-TODAY Anand Kansagra <anandkansagra@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class ResPartnerBank(models.Model):
    """Res Partner Bank."""

    _inherit = 'res.partner.bank'

    type = fields.Selection(selection_add=[('afc', 'AFC')])
    partner2_id = fields.Many2one('res.partner', 'Partner 2')
