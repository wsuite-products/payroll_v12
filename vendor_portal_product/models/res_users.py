# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Kunjal Patel <kunjalpatel@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class ResUsers(models.Model):

    _inherit = 'res.users'

    is_vendor_portal = fields.Boolean(string="Vendor Portal")

    def write(self, vals):
        if self.env.context.get('vendor_portal', False):
            vals.update({'is_vendor_portal': True})
        res = super(ResUsers, self).write(vals)
        return res
