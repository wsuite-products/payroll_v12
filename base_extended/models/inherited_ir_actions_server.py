# Copyright 2020-TODAY Darshan Patel <darshan.barcelona@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class IrActionsServer(models.Model):
    _inherit = "ir.actions.server"

    permission_sent = fields.Boolean()
