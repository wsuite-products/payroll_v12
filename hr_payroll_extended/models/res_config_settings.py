# Copyright 2020-TODAY Anand Kansagra <anandkansagra@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    module_l10n_payroll_co = fields.Boolean(
        string="Allow Payroll Localization Colombia")
