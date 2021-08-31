# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Kunjal Patel <kunjalpatel@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class ResPartner(models.Model):

    _inherit = 'res.partner'

    is_vendor_portal = fields.Boolean(string="Is Vendor Portal")
