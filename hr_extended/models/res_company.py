# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    generate_process_in_other_db = fields.Boolean('Generate Process in other Database?')
