# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Darshan Patel <darshan.barcelona@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sign_digital = fields.Binary('Sign Digital')
    payroll_director = fields.Boolean('Is Payroll Director')
