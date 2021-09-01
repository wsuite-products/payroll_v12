# Copyright 2020-TODAY WSuite Products <wsuite-products@destiny.ws>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class HrYouType(models.Model):
    _name = "hr.you.type"
    _description = "Hr You Type"

    name = fields.Char()
    description = fields.Text()
