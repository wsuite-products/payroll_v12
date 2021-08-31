# Copyright 2020-TODAY Anand Kansagra <anandkansagra@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class HrPayrollConfigParameters(models.Model):
    """Hr Payroll Config Parameters."""

    _name = "hr.payroll.config.parameters"
    _description = "Hr Payroll Config Parameters"

    name = fields.Char()
